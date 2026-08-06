if globals.configDict["JokesMemes"]:

    @client.tree.command(name="businessgraph", description="Creates a business graph for your company or project.")
    @app_commands.describe(graphname="The name of your business graph.")
    @app_commands.describe(successtype="The type of success (Falling, Raising & Flat).")
    @app_commands.describe(label="The plot label name.")
    @app_commands.describe(label="Include business man.")
    async def fakeGraphCommand(interaction: discord.Interaction, graphname:str, successtype: str, label:str = "Investments", man:bool = False):
        if not await isInteractionAuthServer(interaction):
            return

        async def sendHelpEmbed():
            embed = discord.Embed (
                title = "Business Graph Help",
                description = "Generates a basic business graph.",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Parameters:",
                value = """
                graphname - Name of the graph.
                successType - [rise, fall, flat, sky] Specifies the how successful your business is.
                man - Inserts a random business man pointing to your graph more professional.
                label - What type of investment is it? stock? could be anything really. 
                """,
                inline = False
            )

            await interaction.response.send_message(embed=embed)
            logger.info(f"{interaction.user.name} Has executed the fakegraph / help command.")

        if graphname == "":
            await sendHelpEmbed()
            return

        import random
        import matplotlib.pyplot as plt

        dataTable = [0] * 10
        valueOffsetter = 0
        match successtype.lower():
            case "falling" | "fall" | "down":
                valueOffsetter = 1100
                for x in range(0, 10):
                    dataTable[x] = random.randint(valueOffsetter - 25, valueOffsetter + 25)
                    valueOffsetter = int(valueOffsetter / 2)
                
            case "raising" | "rise" | "up":
                for x in range(0, 10):
                    dataTable[x] = random.randint(valueOffsetter - 100, valueOffsetter + 100)
                    valueOffsetter += 100

            case "flat" | "line":
                valueOffsetter = random.randint(100, 400)
                for x in range(0, 10):
                    dataTable[x] = random.randint(valueOffsetter - 1, valueOffsetter + 1)

            case "rocket" | "sky":
                for x in range(0, 10):
                    dataTable[x] = random.randint(valueOffsetter - 200, valueOffsetter + 200)
                    valueOffsetter += 350

            case "rug":
                valueOffsetter = 100
                for x in range(0, 10):
                    if x >= 5:
                        dataTable[x] = 0
                    else:
                        dataTable[x] = random.randint(valueOffsetter - 10, valueOffsetter + 10)
                        valueOffsetter += 5

            case _:
                await sendHelpEmbed()
                return

        plt.figure(figsize=(9, 5))

        plt.plot(
            range(1, len(dataTable) + 1),
            dataTable,
            marker="o",
            label=label,
        )

        plt.title(graphname)
        plt.xlabel("Time")
        plt.ylabel(label)
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
            
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        plt.close()

        buffer.seek(0)

        #Inserts a random business man within the image.
        if man:
            pathCommon = "assets/businessmen/"
            manData = readJson(f"{pathCommon}imageInfo.json")
    
            if manData is None or len(manData) <= 0:
                logger.error("Failed to load Business man image info...")
                return

            choosenKey = random.choice(list(manData.keys()))
            imageData = manData[choosenKey]

            backImage = Image.open(buffer).convert("RGBA")
            foreImage = Image.open(f"{pathCommon}{imageData["path"]}").convert("RGBA")

            xOffset = imageData["offsetX"]
            yOffset = imageData["offsetY"]

            backImage.paste(foreImage, (xOffset, yOffset), foreImage)
            buffer = BytesIO()
            backImage.save(buffer, format="PNG")
            buffer.seek(0)

        await interaction.response.send_message(content=f"Your {graphname} {label} graph.", file = discord.File(buffer, filename="its_just_business.png"))
        logger.info(f"{interaction.user.name} Has executed the fakegraph command.")
