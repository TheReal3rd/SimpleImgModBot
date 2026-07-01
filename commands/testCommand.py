
@client.tree.command(name="test", description="Just a command to test things.")
async def testCommand(interaction: discord.Interaction):
    if not await isInteractionAuthorised(interaction, SERVER_ID):
        return

    view = MyView("This is a param test")
    await interaction.response.send_message("Testing Button", view=view)
    logger.info(f"{interaction.user.name} Has executed the test command.")

        


        


        
