from enum import Enum, auto
import uuid
import discord # type: ignore
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    AWAITING_CATEGORY = auto()
    AWAITING_HARMFUL_CONDUCT_TYPE = auto()
    AWAITING_VIOLENCE_TYPE = auto()
    AWAITING_HATEFUL_DETAILS = auto()
    AWAITING_MINOR_CONFIRMATION = auto()
    AWAITING_ILLEGAL_DETAILS = auto()
    AWAITING_FRAUD_DETAILS = auto()
    AWAITING_SELF_HARM_DETAILS = auto()
    AWAITING_DETAILS = auto()
    AWAITING_ACTION = auto()
    AWAITING_BLOCK_ACTION = auto()
    REPORT_COMPLETE = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.report_id = str(uuid.uuid4())[:8] 
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content.lower() == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say help at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking Copy Message Link."
            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say cancel to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say cancel to cancel."]
            try:
                self.message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say cancel to cancel."]

            # Found the message - show it to the user
            self.state = State.MESSAGE_IDENTIFIED
            return ["I found this message:", "「" + self.message.author.name + ": " + self.message.content + "」"]
        
        # For all other states, we'll let the ModBot class handle the state transitions
        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE