
@client.tree.command(name="blockimg", description="Add an img to the block list.")
@app_commands.describe(url="The URL to the image to add to the ban list.")
async def blockCommand(interaction: discord.Interaction, url: str):

        if not str(interaction.guild.id) == SERVER_ID:
            await interaction.response.send_message("This is not the guild i serve.", ephemeral=True)
            logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You're not an administrator.", ephemeral=True)
            logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
            return

        correctStart = url.startswith("http://") or url.startswith("https://")
        correctEnd = False
        for ext in IMG_EXTENSIONS:
            correctEnd = url.endswith(ext)
            if correctEnd:
                break 

        if correctStart:
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
            
            imageSHA256, imagePerceptual, emb = calcImageHash(imageBytes)

            if imageSHA256 in bannedImageDict.keys():
                await interaction.response.send_message("The image is already in the banned list...", ephemeral=True)
            else:
                emoji = discord.utils.get(interaction.guild.emojis, name="ThumbsUp")

                logger.info(f"Image has been manually added by {interaction.user.name} sha256: {imageSHA256} phash: {imagePerceptual}")
                await interaction.response.send_message(f"The requested image has been added to the banned list. {str(emoji)}")
                databaseManager.add(imageSHA256, imagePerceptual, emb)
                
        else:
            errMsg = "Failed to pass the URL checks. Ensure the URL is correctly formatted."
            await interaction.response.send_message(errMsg, ephemeral=True)
            logger.info(f"Attempted admin command called by: {interaction.user.name} MSG: {errMsg}.")

        


        
