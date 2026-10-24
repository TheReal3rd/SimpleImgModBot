
if globals.configDict["SaveImages"]:

    @client.tree.command(name="savedimg", description="Manage and observe saved images.")
    @app_commands.describe(action="The action to be taken.")
    @app_commands.describe(imagesha="The image sha256 to view or delete.")
    @app_commands.describe(force="Force execute the selected operation.")
    async def savedImgCommand(interaction: discord.Interaction, action: str = "", imagesha: str = "", force: bool = False):
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
                del - Delete the image.
                list - Lists all images sha and date.
                cleanup - Runs auto cleanup.
                """,
                inline = False
            )

            await interaction.response.send_message(embed = embed)
            logger.info(f"{interaction.user.name} Has executed the savedimg command - viewing help options.")


        async def validSHA(sha256):
            if sha256.strip() == "":
                await interaction.response.send_message("The image argument is empty...")
                logger.info(f"{interaction.user.name} Has executed the savedimg command - No SHA256 has been provided.")
                return False

            if len(sha256) != globals.SHA256_CHAR_LEN:
                await interaction.response.send_message("The provided SHA256 isn't upto expected length requirements.")
                logger.info(f"{interaction.user.name} Has executed the savedimg command - Provided SHA256 doesn't meet length expectations.")
                return False

            return True

        if action == "":
            await sendHelpEmbed()
            return

        match(action.lower()):
            case "cv" | "collage" | "collageview":
                """
                TODO
                1. Image collage frame.
                2. Image scaling to collage template sizes.
                3. Check if the image it 8mb or above. If above then linearly downscale until below or equal to 8mb.
                4. send it with action view. Buttons numbered for each image in frame. max number of buttons?
                5. Delete or handle the required action for the selected image.
                6. be happy.
                """
                
                imagesPaths = imageManager.getImageList()

                if len(imagesPaths) <= 5:
                    await interaction.response.send_message("Too few images saved to create a collage.")
                    logger.info(f"{interaction.user.name} Has executed the savedimg command - Collage view was executed done nothing too few images.")
                    return

                largestPath = ""
                largestImageSize = (-1, -1)
                totalWidth = 0
                totalHeight = 0 

                for path in imagesPaths:
                    with Image.open(path["path"]) as img:
                        width, height = img.size
                        
                        if width > largestImageSize[0] and height > largestImageSize[1]:
                            largestImageSize = (width, height)
                            largestPath = path

                        totalWidth += width
                        totalHeight += height

                avgWidth = totalWidth / len(imagesPaths)
                avgHeight = totalHeight / len(imagesPaths)



                testImage = Image.new("RGB", (1000, 1000), color = "black")
                testDraw = ImageDraw.Draw(testImage)

                testDraw.text((10, 10), "TEST", fill="white")

                buffer = BytesIO()
                testImage.save(buffer, format="PNG")
                buffer.seek(0)

                await interaction.response.send_message("Collage view WIP", file = discord.File(buffer, filename="collageView.png"))
                logger.info(f"{interaction.user.name} Has executed the savedimg command - Collage view was executed...")
            
            case "ls" | "list":
                imageList = imageManager.getImageList()
                listLength = len(imageList)
                if listLength <= 0:
                    await interaction.response.send_message("There are no images saved.")
                    logger.info(f"{interaction.user.name} Has executed the savedimg command - No images have been saved.")
                    return

                listFormat = f"Total: {listLength}.\n"

                for image in imageList:
                    date = image["date"]
                    sha = image["sha"]
                    listFormat += f"{date[0]}-{date[1]}-{date[2]}: {sha}\n"

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

                result: bool = imageManager.removeImage(imagesha)
                if result:
                    await interaction.response.send_message("The requested image has been deleted.")
                    logger.info(f"{interaction.user.name} Has executed the savedimg command - Deleted the requested image: {imagesha}.")
                else:
                    await interaction.response.send_message("Failed to delete the requested image.")
                    logger.info(f"{interaction.user.name} Has executed the savedimg command - Failed to delete the requested image: {imagesha}.")
               
            case "view" | "inspect" | "v":
                if not await validSHA(imagesha):
                    return

                imagePath = imageManager.getImage(imagesha)

                if not imagePath:
                    await interaction.response.send_message("The requested image does not exist in the storage.")
                    logger.info(f"{interaction.user.name} Has executed the savedimg command - Failed to find the requested image possible doesn't exist.")
                    return

                await interaction.response.send_message("The requested image:", file=discord.File(imagePath[1]))
                logger.info(f"{interaction.user.name} Has executed the savedimg command - Posted a image for view request.")
            
            case "cleanup" | "clean":
                imageManager.cleanup(force)
                
                await interaction.response.send_message("A cleanup operation has been ran." if not force else "A force cleanup operation has been ran.")
                logger.info(f"{interaction.user.name} Has executed the savedimg command - Cleanup command.")
            
            case _:
                await sendHelpEmbed()

        


        
