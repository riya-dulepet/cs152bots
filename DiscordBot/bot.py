# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report, State
import pdb
from moderator import ModeratorHandler

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
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
            "Religious hate or bigotry",
            "Other"
        ]

        self.violence_categories = [
            "Showing violence, death, severe injury",
            "Credible threat to safety",
            "Terrorism / Organized Crime",
            "Exploitation",
            "Animal Abuse",
            "Other"
        ]

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
            if message.content.strip() == "1" or message.content.lower() == "yes":
                self.report_data[author_id]["age_under_18"] = True
            elif message.content.strip() == "2" or message.content.lower() == "no":
                self.report_data[author_id]["age_under_18"] = False
            else:
                responses = ["Please select 1 for Yes or 2 for No."]
                for r in responses:
                    await message.channel.send(r)
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
        """Submit a completed report to the moderators"""
        # Get report data
        report_data = self.report_data[author_id]
        reported_message = report_data["reported_message"]
        
        mod_channel = self.mod_channels[reported_message.guild.id]
        report_id = self.reports[author_id].report_id
        
        # Create an embed for the report
        embed = discord.Embed(title="Message Reported", color=discord.Color.red())
        embed.add_field(name="Content", value=reported_message.content, inline=False)
        embed.add_field(name="Author", value=reported_message.author.mention, inline=True)
        embed.add_field(name="Channel", value=reported_message.channel.mention, inline=True)
        embed.add_field(name="Reported by", value=f"<@{author_id}>", inline=True)
        
        # Add report categories
        embed.add_field(name="Category", value=report_data["category"], inline=True)
        
        if "subcategory" in report_data and report_data["subcategory"]:
            embed.add_field(name="Subcategory", value=report_data["subcategory"], inline=True)
            
        if "violence_type" in report_data and report_data["violence_type"]:
            embed.add_field(name="Violence Type", value=report_data["violence_type"], inline=True)
            
        if "hateful_type" in report_data and report_data["hateful_type"]:
            embed.add_field(name="Hateful Conduct Type", value=report_data["hateful_type"], inline=True)
            
        if "illegal_type" in report_data and report_data["illegal_type"]:
            embed.add_field(name="Illegal Item Type", value=report_data["illegal_type"], inline=True)
            
        if "fraud_type" in report_data and report_data["fraud_type"]:
            embed.add_field(name="Fraud/Spam Type", value=report_data["fraud_type"], inline=True)
            
        if "self_harm_type" in report_data and report_data["self_harm_type"]:
            embed.add_field(name="Self-Harm Type", value=report_data["self_harm_type"], inline=True)
            
        if "age_under_18" in report_data and report_data["age_under_18"] is not None:
            embed.add_field(name="Involves minor under 18", value="Yes" if report_data["age_under_18"] else "No", inline=True)
            
        # Add additional details
        if "additional_details" in report_data and report_data["additional_details"]:
            embed.add_field(name="Additional Details", value=report_data["additional_details"], inline=False)
            
        # Add user actions
        if "actions" in report_data and report_data["actions"]:
            embed.add_field(name="User Actions", value=", ".join(report_data["actions"]), inline=False)
        
        embed.add_field(name="Report ID", value=report_id, inline=False)

            
        # Add message link
        message_link = f"https://discord.com/channels/{reported_message.guild.id}/{reported_message.channel.id}/{reported_message.id}"
        embed.add_field(name="Message Link", value=f"[Click to view]({message_link})", inline=False)
        
        # Send the report to moderators
        await mod_channel.send(embed=embed)


        self.pending_mod_reviews[mod_channel.guild.id] = {
        "report_id": report_id,
        "step": "awaiting_severity",
        "data": {
            "report_data": report_data,
            "severity": None,
            "observations": ""
            }
        }

        await mod_channel.send(
            f"🛡️ Moderators: Please assess **severity (1 = low, 2 = medium, 3 = high)** for report `{report_id}`."
        )
            

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        # Forward the message to the mod channel
        mod_channel = self.mod_channels[message.guild.id]
        await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')
        scores = self.eval_text(message.content)
        await mod_channel.send(self.code_format(scores))
    
    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return message

    
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

        if category == "Violence or Hateful Conduct" and sub == "Violence":
            if severity == 3 or violence == "Credible threat to safety":
                action = "Escalated to legal team and safety specialists."
            elif violence == "Exploitation" and involves_minor:
                action = "Child exploitation — reported to child safety unit."
            else:
                action = "Warning issued. Message removed."

        elif category == "Hateful Conduct":
            action = "Hateful conduct confirmed. User suspended."

        elif category == "Suicide, self-injury, or eating disorders":
            action = "Referred to mental health support."

        elif category == "Fraud, Scam, or Spam":
            action = "Scam detected. User shadowbanned."
        
        elif category == "Promoting or selling illegal items":
            illegal_type = report_data.get("illegal_type", "").lower()

            if severity == 3 and illegal_type in ["weapons", "drugs"]:
                action = "High-severity illegal content detected. Case escalated to law enforcement specialists."
            else:
                action = "Cntent removed. No further action taken at this time."

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