
@client.tree.command(name="hello", description="Say hello")
async def helloCommand(interaction: discord.Interaction):
    RESENFOR_ID = 332634195941654529
    if interaction.user.id == RESENFOR_ID:
        resenforNames = ["Smelly", "Stinky", "Low", "Bad", "Ew", "Yuck", "Blah"]
        NAME_LENGTH = len(resenforNames)
        await interaction.response.send_message(
            f"Hello, {resenforNames[random.randint(0, NAME_LENGTH - 1)]} {interaction.user.mention}!"
        )
    else:
        await interaction.response.send_message(
            f"Hello, {interaction.user.mention}!"
        )
