import discord # type: ignore

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
        embed.add_field(
            name="Involves minor under 18",
            value="Yes" if report_data["age_under_18"] else "No",
            inline=True
        )
        
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