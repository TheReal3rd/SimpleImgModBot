
@client.tree.command(name="cleanup", description="Used to clean up pending checks and bans.")
@app_commands.describe(table="The name of the table to clean up.")
async def cleanupCommand(interaction: discord.Interaction, table: str):
    if not isInteractionAuthorised(interaction):
        return

    if table.lower() in Tables:
        result = pendingDatabaseManager.deleteTable(table)

        msg = f"{table} has been cleared of all pending tasks."

        await interaction.response.send_message(msg)
        logger.info(f"Clean up executed by: {interaction.user.name} With message of: {msg}")
    else:
        await interaction.response.send_message("Provided table name doesn't exist.")
        logger.info(f"Clean up executed by: {interaction.user.name} Failed to provide a correct table name.")

    return

    
        
