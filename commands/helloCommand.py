resenforNames = ["Smelly", "Stinky", "Low", "Bad", "Ew", "Yuck", "Blah"]
NAME_LENGTH = len(resenforNames)
RESENFOR_ID = 332634195941654529

@client.tree.command(name="hello", description="Say hello")
async def helloCommand(interaction: discord.Interaction):
    if interaction.user.id == RESENFOR_ID:
        await interaction.response.send_message(
            f"Hello, {resenforNames[random.randint(0, NAME_LENGTH - 1)]} {interaction.user.mention}!"
        )
    else:
        await interaction.response.send_message(
            f"Hello, {interaction.user.mention}!"
        )
