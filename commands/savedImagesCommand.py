
if globals.configDict["SaveImages"]:

    @client.tree.command(name="savedimg", description="Manage and observe saved images.")
    @app_commands.describe(action="The action to be taken.")
    @app_commands.describe(imagesha="The image sha256 to view or delete.")
    async def savedImgCommand(interaction: discord.Interaction, action: str = "", imagesha: str = ""):
        if not await isInteractionAuthorised(interaction):
            return

        # TODO make a multi image viewer by rendering a image collage with some sort of identifer

        action = action.strip()
        imageManager = globals.imageManager

        async def sendHelpEmbed():
            embed = discord.Embed (
                title = "Saved Images",
                description = f"Images {imageManager.imageCount()}.",
                color=discord.Color.red()
            )

            embed.add_field(
                name="Commands:",
                value = f"""
                view - View the saved image.
                del - Del the image.
                list - Lists all images sha and date.
                """,
                inline = False
            )

            await interaction.response.send_message(embed = embed)
            logger.info(f"{interaction.user.name} Has executed the savedimg command - viewing help options.")


        async def validSHA(sha256):
            if sha256.strip() == "":
                await interaction.response.send_message("The image argument is empty...")
                logger.info(f"{interaction.user.name} Has executed the savedimg command - No arguments have been provided.")
                return False

            length = len(sha256)
            shaLength = globals.SHA256_CHAR_LEN
            if length < shaLength or length > shaLength:
                await interaction.response.send_message("The provided SHA256 isn't upto expected length requirements.")
                logger.info(f"{interaction.user.name} Has executed the savedimg command - No arguments have been provided.")
                return False

            return True

        if action == "":
            await sendHelpEmbed()
            return

        match(action):
            case "ls" | "list":
                imageList = imageManager.getImageList()
                if len(imageList) <= 0:
                    await interaction.response.send_message("There are no images saved.")
                    logger.info(f"{interaction.user.name} Has executed the savedimg command - No images have been saved.")
                    return

                listFormat = f"Total: {imageManager.imageCount()}.\n"

                for key, value in imageList.items():
                    listFormat += f"{value[0]}-{value[1]}-{value[1]}: {key}\n"

                if len(listFormat) >= globals.EMBED_LEN_LIMIT:
                    await interaction.response.send_message("The response would be too big...")
                    return

                embed = discord.Embed (
                    title = "Saved Images",
                    description = f"{listFormat}",
                    color=discord.Color.red()
                )

                await interaction.response.send_message(embed = embed)
                logger.info(f"{interaction.user.name} Has executed the savedimg command - Image list has been posted.")
            
            case "del" | "delete" | "rm":
                if not await validSHA(imagesha):
                    return

                imageManager.removeImage(imagesha)
                await interaction.response.send_message("The requested image has been deleted.")
                logger.info(f"{interaction.user.name} Has executed the savedimg command - Deleted the requested image: {imagesha}.")
               
            case "view" | "inspect" | "v":
                if not await validSHA(imagesha):
                    return

                imagePath = imageManager.getImage(imagesha)

                if imagePath == None:
                    await interaction.response.send_message("The requested image does not exist in the storage.")
                    logger.info(f"{interaction.user.name} Has executed the savedimg command - Failed to find the requested image possible doesn't exist.")
                    return

                await interaction.response.send_message("The requested image:", file=discord.File(imagePath[1]))
                logger.info(f"{interaction.user.name} Has executed the savedimg command - Posted a image for view request.")
            case _:
                await sendHelpEmbed()

        


        
