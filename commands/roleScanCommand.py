
@client.tree.command(name="rolescan", description="Scans the server's member list for members who're missing required roles.")
@app_commands.describe(maxlimit="The max number members to be within the list to return the results table.")
async def scanCommand(interaction: discord.Interaction, maxlimit: int = 0):
    if not await isInteractionAuthorised(interaction):
        return

    guild = client.get_guild(globals.SERVER_ID)
    if not guild:
        guild = await client.fetch_guild(globals.SERVER_ID)

    if guild is None:
        msg = "Failed to find the guild?"
        logger.info(f"Roles scan called by: {interaction.user.name} {msg}")
        await interaction.response.send_message(msg)
        return

    requiredRoleID = globals.configDict["RequiredRoleID"]
    if not requiredRoleID or requiredRoleID.strip() == "":
        msg = "No required Role ID provided."
        logger.info(f"Roles scan called by: {interaction.user.name} {msg}")
        await interaction.response.send_message(msg)
        return

    numMemberChecked: int = 0
    badUserDict: dict = {}
    async for member in guild.fetch_members(limit=maxlimit):
        numMemberChecked += 1
        badAccount = True

        if member.bot:
            continue

        if member.guild_permissions.administrator:
            continue

        for role in member.roles:
            if str(role.id) == requiredRoleID:
                badAccount = False
                continue 

        if badAccount:
            badUserDict[member.id] = {
                "name" : member.name,
                "displayName" : member.display_name
            }

    msg = ""
    logger.info(f"{interaction.user.name} Has executed the role scan command.")
    if len(badUserDict) <= 0:
        msg = "No users are missing roles. Looks good."
        logger.info(f"Roles scan called by: {interaction.user.name} {msg}")
        responseMSG = await interaction.response.send_message(msg)
    else:
        view = RequiredRoleUserView(badUserDict)

        for key in badUserDict.keys():
            userData = badUserDict[key]
            msg += f"ID: {key} Name: {userData["name"]} DName: {userData["displayName"]}\n"

        if len(msg) >= globals.EMBED_LEN_LIMIT:
            import io
            file = discord.File(
                fp=io.BytesIO(msg.encode("utf-8")),
                filename = "results.txt",
            )
            await interaction.response.send_message("The result list was longer then the embed limit.", file=file, view=view)
            return

        embed = discord.Embed (
            title = "Results",
            description = msg,
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, view=view)
    return