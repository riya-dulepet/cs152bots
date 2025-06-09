# This handles the moderator side of the flow

class ModeratorHandler:
    def __init__(self, bot):
        self.bot = bot

    async def handle_moderator_command(self, message):
        guild_id = message.guild.id

        if guild_id not in self.bot.pending_mod_reviews:
            return

        pending = self.bot.pending_mod_reviews[guild_id]
        report_id = pending["report_id"]
        step = pending["step"]
        mod_data = pending["data"]

        if step == "awaiting_severity":
            try:
                severity = int(message.content.strip())
                if severity not in [1, 2, 3]:
                    raise ValueError
            except ValueError:
                await message.channel.send("❗ Please enter a number from 1 to 3 for severity.")
                return

            mod_data["severity"] = severity
            pending["step"] = "awaiting_observations"
            await message.channel.send("📝 Please enter any moderator observations (or say `none`).")

        elif step == "awaiting_observations":
            mod_data["observations"] = message.content.strip()
            await self.bot.finalize_moderation_decision(
                report_data=mod_data["report_data"],
                severity=mod_data["severity"],
                observations=mod_data["observations"],
                channel=message.channel
            )
            del self.bot.pending_mod_reviews[guild_id]
