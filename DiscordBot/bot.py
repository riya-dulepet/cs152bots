import discord # type: ignore
from discord.ext import commands # type: ignore
import os
import json
import logging
import re
import requests
from report import Report, State
import pdb
from moderator import ModeratorHandler
from report_submission import submit_report

from openai import OpenAI, OpenAIError # type: ignore
from dotenv import load_dotenv
load_dotenv()

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    tokens = json.load(f)
    discord_token = tokens['discord']

class ModBot(discord.Client):
    def __init__(self): 
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.report_data = {} # Map from user IDs to their report data
        self.pending_mod_reviews = {} 
        self.moderator_handler = ModeratorHandler(self)

        with open("../automated_model/model_apis/prompts_created/both/prompt_long_1.txt", "r") as f:
            self.llm_prompt_template = f.read()
        

        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.categories = [
            "I just don't like it",
            "Promoting or selling illegal items",
            "Fraud, Scam, or Spam",
            "Other",
            "Suicide, self-injury, or eating disorders",
            "Violence or Hateful Conduct",
        ]
        self.illegal_categories = [
            "Weapons",
            "Drugs",
            "Other"
        ]
        self.fraud_categories = [
            "Spam",
            "Fraud/Scam",
        ]
        self.suicide_categories = [
            "Expressing suicidal thoughts",
            "Promoting self-harm",
            "Promoting or glorifying eating disorders"
        ]
        self.violence_or_hate = ["Violence", "Hateful Conduct"]
        self.hateful_conduct_categories = [
            "Other",
            "Slurs/Offensive Symbols",
            "Exploitation",
            "Racist or xenophobic content",
            "Religious hate or bigotry",        ]

        self.violence_categories = [
            "Showing violence, death, severe injury",
            "Credible threat to safety",
            "Terrorism / Organized Crime",
            "Exploitation",
            "Animal Abuse",
            "Other"
        ]

        self.flagged_messages = set()         


    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel
        

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild and message.channel.name == f'group-{self.group_num}-mod':
            await self.moderator_handler.handle_moderator_command(message)
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the report command to begin the reporting process.\n"
            reply += "Use the cancel command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)
            self.report_data[author_id] = {
                "reported_message": None,
                "category": None,
                "subcategory": None,
                "details": None,
                "age_under_18": None,
                "actions": [],
                "author_id": author_id
            }

        # Process the current state and update based on user input
        if self.reports[author_id].state == State.REPORT_START:
            responses = await self.reports[author_id].handle_message(message)
            
        elif self.reports[author_id].state == State.AWAITING_MESSAGE:
            responses = await self.reports[author_id].handle_message(message)
            reported_msg = self.reports[author_id].message
            if reported_msg.id in self.flagged_messages:
                await message.channel.send("⚠️ This message has already been reported and is under review.")
                self.reports[author_id].state = State.REPORT_COMPLETE
                return

            
        if self.reports[author_id].state == State.MESSAGE_IDENTIFIED:
            # Store the reported message
            self.report_data[author_id]["reported_message"] = self.reports[author_id].message
            
            # Present category options
            reply = "Please indicate why you are reporting this message:"
            for i, category in enumerate(self.categories):
                reply += f"\n{i+1}. {category}"
            responses.append(reply)
            
            # Update state
            self.reports[author_id].state = State.AWAITING_CATEGORY
            
        elif self.reports[author_id].state == State.AWAITING_CATEGORY:
            try:
                # Parse the category selection
                selection = int(message.content.strip())
                if 1 <= selection <= len(self.categories):
                    category = self.categories[selection-1]
                    self.report_data[author_id]["category"] = category

                    if category == "I just don't like it":    
                        # Go straight to additional details
                        responses = ["Please include any additional details to DM to the bot"]
                        self.reports[author_id].state = State.AWAITING_DETAILS
                        
                    elif category == "Promoting or selling illegal items":
                        # Ask what's being promoted
                        reply = "What is being promoted or sold?"
                        for i, subcategory in enumerate(self.illegal_categories): 
                            reply += f"\n{i+1}. {subcategory}"
                        
                        responses = [reply]
                        self.reports[author_id].state = State.AWAITING_ILLEGAL_DETAILS   

                    elif category == "Fraud, Scam, or Spam":
                        # Ask which best describes the problem
                        reply = "Which best describes the problem?"
                        for i, subcategory in enumerate(self.fraud_categories): 
                            reply += f"\n{i+1}. {subcategory}"
                        responses = [reply]
                        self.reports[author_id].state = State.AWAITING_FRAUD_DETAILS
                    
                    elif category == "Suicide, self-injury, or eating disorders":
                        reply = "Please call 988 if it is urgent. What best describes your content?"
                        for i, subcategory in enumerate(self.suicide_categories): 
                            reply += f"\n{i+1}. {subcategory}"
                        responses = [reply]
                        self.reports[author_id].state = State.AWAITING_SELF_HARM_DETAILS

                    elif category == "Violence or Hateful Conduct":
                        # Ask for subcategory of harmful conduct
                        reply = "Which best describes the problem?"
                        for i, subcategory in enumerate(self.violence_or_hate):
                            reply += f"\n{i+1}. {subcategory}"
                        responses = [reply]
                        self.reports[author_id].state = State.AWAITING_HARMFUL_CONDUCT_TYPE
                                        
                    else:  # Other
                        # Go straight to additional details
                        responses = ["Please include any additional details to DM to the bot"]
                        self.reports[author_id].state = State.AWAITING_DETAILS
                else:
                    responses = ["Please select a valid option between 1 and " + str(len(self.categories))]
            except ValueError:
                responses = ["Please enter a number to select a category."]
                
        elif self.reports[author_id].state == State.AWAITING_HARMFUL_CONDUCT_TYPE:
            try:
                selection = int(message.content.strip())
                if 1 <= selection <= len(self.violence_or_hate):
                    subcategory = self.violence_or_hate[selection-1]
                    self.report_data[author_id]["subcategory"] = subcategory
                    
                    # Handle different subcategory flows
                    if subcategory == "Violence":
                        # Ask for violence type
                        reply = "What does this violence entail?"
                        for i, violence_type in enumerate(self.violence_categories):
                            reply += f"\n{i+1}. {violence_type}"
                        responses = [reply]
                        self.reports[author_id].state = State.AWAITING_VIOLENCE_TYPE
                    else:
                        # For other harmful conduct subcategories, go to details
                        reply = "What best describes the harmful conduct?"
                        for i, hate_type in enumerate(self.hateful_conduct_categories):
                            reply += f"\n{i+1}. {hate_type}"
                        responses = [reply]
                        self.reports[author_id].state = State.AWAITING_HATEFUL_DETAILS
                else:
                    responses = ["Please select a valid option between 1 and " + str(len(self.violence_or_hate))]
            except ValueError:
                responses = ["Please enter a number to select a subcategory."]
                
        elif self.reports[author_id].state == State.AWAITING_VIOLENCE_TYPE:
            try:
                selection = int(message.content.strip())
                if 1 <= selection <= len(self.violence_categories):
                    violence_type = self.violence_categories[selection-1]
                    self.report_data[author_id]["violence_type"] = violence_type
                    
                    if violence_type == "Exploitation":
                        # Ask if it involves minors
                        responses = ["Does this involve someone under the age of 18?", 
                                    "1. Yes", 
                                    "2. No"]
                        self.reports[author_id].state = State.AWAITING_MINOR_CONFIRMATION
                    else:
                        # Move to additional details
                        responses = ["Please include any additional details to DM to the bot"]
                        self.reports[author_id].state = State.AWAITING_DETAILS
                else:
                    responses = ["Please select a valid option between 1 and " + str(len(self.violence_categories))]
            except ValueError:
                responses = ["Please enter a number to select a violence type."]
        
        elif self.reports[author_id].state == State.AWAITING_HATEFUL_DETAILS:
            try:
                selection = int(message.content.strip())
                if 1 <= selection <= len(self.hateful_conduct_categories):
                    hateful_type = self.hateful_conduct_categories[selection-1]
                    self.report_data[author_id]["hateful_type"] = hateful_type
                    
                    # Move to additional details
                    responses = ["Please include any additional details to DM to the bot"]
                    self.reports[author_id].state = State.AWAITING_DETAILS
                else:
                    responses = ["Please select a valid option between 1 and " + str(len(self.hateful_conduct_categories))]
            except ValueError:
                responses = ["Please enter a number to select a category."]
                
        elif self.reports[author_id].state == State.AWAITING_ILLEGAL_DETAILS:
            try:
                selection = int(message.content.strip())
                if 1 <= selection <= len(self.illegal_categories):
                    illegal_type = self.illegal_categories[selection-1]
                    self.report_data[author_id]["illegal_type"] = illegal_type
                    
                    # Move to additional details
                    responses = ["Please include any additional details to DM to the bot"]
                    self.reports[author_id].state = State.AWAITING_DETAILS
                else:
                    responses = ["Please select a valid option between 1 and " + str(len(self.illegal_categories))]
            except ValueError:
                responses = ["Please enter a number to select a category."]
                
        elif self.reports[author_id].state == State.AWAITING_FRAUD_DETAILS:
            try:
                selection = int(message.content.strip())
                if 1 <= selection <= len(self.fraud_categories):
                    fraud_type = self.fraud_categories[selection-1]
                    self.report_data[author_id]["fraud_type"] = fraud_type
                    
                    # Move to additional details
                    responses = ["Please include any additional details to DM to the bot"]
                    self.reports[author_id].state = State.AWAITING_DETAILS
                else:
                    responses = ["Please select a valid option between 1 and " + str(len(self.fraud_categories))]
            except ValueError:
                responses = ["Please enter a number to select a category."]
                
        elif self.reports[author_id].state == State.AWAITING_SELF_HARM_DETAILS:
            try:
                selection = int(message.content.strip())
                if 1 <= selection <= len(self.suicide_categories):
                    self_harm_type = self.suicide_categories[selection-1]
                    self.report_data[author_id]["self_harm_type"] = self_harm_type
                    
                    # Move to additional details
                    responses = ["Please include any additional details to DM to the bot"]
                    self.reports[author_id].state = State.AWAITING_DETAILS
                else:
                    responses = ["Please select a valid option between 1 and " + str(len(self.suicide_categories))]
            except ValueError:
                responses = ["Please enter a number to select a category."]
                
        elif self.reports[author_id].state == State.AWAITING_MINOR_CONFIRMATION:
            content = message.content.strip().lower()
            if content in ["1", "yes", "y"]:
                self.report_data[author_id]["age_under_18"] = True
            elif content in ["2", "no", "n"]:
                self.report_data[author_id]["age_under_18"] = False
            else:
                await message.channel.send(f"Please select a valid option between 1 and {len(self.violence_categories)}")
                return
               
            # Move to additional details
            responses = ["Please include any additional details to DM to the bot"]
            self.reports[author_id].state = State.AWAITING_DETAILS
                
        elif self.reports[author_id].state == State.AWAITING_DETAILS:
            # Store the additional details
            self.report_data[author_id]["additional_details"] = message.content
            
            # Finish the report and show available actions
            responses = [
                "Thank you for reporting and keeping our community safe. Our content moderation team will review the report and decide on it.",
                "You may also block the user from interacting and viewing our community standards below:",
                "1. Block User",
                "2. View community standards",
            ]
            self.reports[author_id].state = State.AWAITING_ACTION
            
        elif self.reports[author_id].state == State.AWAITING_ACTION:
            action = None
            if message.content.strip() == "1":
                action = "Block User"
                responses = ["You can block them directly at their profile. Once you do so, they won't be able to find your profile, posts, or interact with you.", 
                            "1. View Profile",
                            "2. Cancel"]
                self.reports[author_id].state = State.AWAITING_BLOCK_ACTION
                
            elif message.content.strip() == "2":
                action = "View community standards"
                responses = ["https://discord.com/guidelines"]
                self.reports[author_id].state = State.REPORT_COMPLETE
                
            else:
                responses = ["Please select a valid option between 1 and 2."]
                for r in responses:
                    await message.channel.send(r)
                return
            
            # Store the selected action
            self.report_data[author_id]["actions"].append(action)
            
            if action == "View community standards":
                # Submit the report to moderators
                await self.submit_report(author_id)
                
        elif self.reports[author_id].state == State.AWAITING_BLOCK_ACTION:
            action = None
            if message.content.strip() == "1":
                action = "View Profile"
                responses = ["Here is the user's profile (simulated)."]
                self.reports[author_id].state = State.REPORT_COMPLETE
                
            elif message.content.strip() == "2":
                action = "Cancel"
                responses = ["Block action cancelled."]
                self.reports[author_id].state = State.REPORT_COMPLETE
                
            else:
                responses = ["Please select a valid option between 1 and 2."]
                for r in responses:
                    await message.channel.send(r)
                return
            
            # Store the selected action
            self.report_data[author_id]["actions"].append(action)
            
            # Submit the report to moderators
            await self.submit_report(author_id)
            
        # Send all responses to the user
        for r in responses:
            await message.channel.send(r)

    async def submit_report(self, author_id):
        await submit_report(self, author_id)
    


    def map_llm(self, result):
        llm_map = {
        "MISOGYNISTIC": ("Violence or Hateful Conduct", "Hateful Conduct"),
        "NON-MISOGYNISTIC": ("I just don't like it", "Other"),
        }

        cat, sub = llm_map.get(
            result.get("label", "NON-MISOGYNISTIC"), ("Other", "Other")
        )
        return {
            "category": cat,
            "subcategory": sub,
            "severity": int(result.get("severity", 2)),
            "hateful_type": result.get("category"),
            "confidence": result.get("confidence"),
        }
                

    async def handle_channel_message(self, message):
        if message.channel.name != f'group-{self.group_num}':
            return

        mod_channel = self.mod_channels[message.guild.id]
        await mod_channel.send(f'Forwarded:\n{message.author}: “{message.content}”')

        result = self.eval_text(message.content)

        await mod_channel.send(
            f"🚨 **LLM flagged** – {result}"
        )
        if result.get("label") == "MISOGYNISTIC":
            mapped = self.map_llm(result)

            author_id = message.author.id
            self.report_data[author_id] = {
                "reported_message": message,
                **mapped,
                "details": f"Auto‑flagged (conf {mapped['confidence']:.2})",
                "actions": ["Auto‑flagged by LLM"],
                "author_id": author_id,
            }

            self.flagged_messages.add(message.id)
            await self.finalize_moderation_decision(
                report_data=self.report_data[author_id],
                severity=mapped["severity"],
                observations="Automated LLM decision",
                channel=mod_channel,
            )
    
    def eval_text(self, message_text: str):
        prompt = f"{self.llm_prompt_template}\n\n-----\nMessage:\n{message_text}\n-----"

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content.strip()

            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                print("[LLM Parse Error] Response:", content)
                return {"flagged": False}

            return parsed  # Contains label, category, confidence, severity

        except OpenAIError as e:
            print("[LLM API Error]", e)
            return {"flagged": False}

    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text+ "'"

    async def finalize_moderation_decision(self, report_data, severity, observations, channel):
        category = report_data.get("category", "")
        sub = report_data.get("subcategory", "")
        violence = report_data.get("violence_type", "")
        involves_minor = report_data.get("age_under_18", False)

        if severity == 1: 
            action = "Content reviewed. No further action required."
        
        elif severity == 2: 
            action = "Warning issued. Message removed."

        else: 
            if category == "Violence or Hateful Conduct" and sub == "Violence":
                if violence == "Credible threat to safety":
                    action = "Escalated to legal team and safety specialists."
                elif violence == "Exploitation" and involves_minor:
                    action = "Child exploitation — reported to child safety unit."
                else:
                    action = "Warning issued. Message removed."

            elif category == "Violence or Hateful Conduct" and sub == "Hateful Conduct":
                action = "Hateful conduct confirmed. User suspended."

            elif category == "Suicide, self-injury, or eating disorders":
                action = "Referred to mental health support."

            elif category == "Fraud, Scam, or Spam":
                action = "Scam detected. User shadowbanned."
            
            elif category == "Promoting or selling illegal items":
                illegal_type = report_data.get("illegal_type", "").lower()

                if illegal_type in ["weapons", "drugs"]:
                    action = "High-severity illegal content detected. Case escalated to law enforcement specialists."
                else:
                    action = "Content removed. No further action taken at this time."

            elif category == "I just don't like it":
                action = "ℹReport dismissed. No action taken."
            else: 
                action = "Content reviewed. No further action required."

        # Compose summary
        summary = f"""**Moderator Decision Summary**
        - **Category:** {category}
        - **Severity:** {severity}
        - **Moderator Notes:** {observations}
        - **Action Taken:** {action}
        """

        await channel.send(summary)

        author_id = report_data.get("author_id")
        if author_id:
            user = await self.fetch_user(author_id)
            await user.send("✅ Your report has been reviewed. Here is the outcome:")
            await user.send(summary)


client = ModBot()
client.run(discord_token)