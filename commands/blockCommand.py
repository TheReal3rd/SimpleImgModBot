
@client.tree.command(name="blockimg", description="Add an img to the block list.")
@app_commands.describe(url="The URL to the image to add to the ban list.")
async def blockCommand(interaction: discord.Interaction, url: str):
        if not await isInteractionAuthorised(interaction):
            return

        correctStart = url.startswith("http://") or url.startswith("https://")

        if "&" in url:
            urlSplit = url.split("?")[0]
        else:
            urlSplit = url

        correctEnd = False
        for ext in globals.IMG_EXTENSIONS:
            correctEnd = urlSplit.endswith(ext)
            if correctEnd:
                break 

        if correctStart and correctEnd:
            import requests

            headResponse = requests.head(url)
            contentType = headResponse.headers.get("Content-Type")

            if not contentType.startswith("image/"):
                errMsg = "Response headers declared the content as not being an image."
                await interaction.response.send_message(errMsg, ephemeral=True)
                logger.warning(f"Attempted admin command called by: {interaction.user.name} MSG: {errMsg}.")
                return

            response = requests.get(url)
            response.raise_for_status()

            imageBytes = response.content
            
            imageSHA256, emb = calcImageHash(imageBytes)

            dbCheck = databaseManager.get(imageSHA256)
            if dbCheck != None:
                await interaction.response.send_message("The image is already in the banned list...", ephemeral=True)
            else:
                emoji = discord.utils.get(interaction.guild.emojis, name="ThumbsUp")

                logger.info(f"Image has been manually added by {interaction.user.name} sha256: {imageSHA256}")
                await interaction.response.send_message(f"The requested image has been added to the banned list. {str(emoji)}")
                databaseManager.add(imageSHA256, emb)
                
        else:
            errMsg = "Failed to pass the URL checks. Ensure the URL is correctly formatted."
            await interaction.response.send_message(errMsg, ephemeral=True)
            logger.info(f"Attempted admin command called by: {interaction.user.name} MSG: {errMsg}.")

        


        
