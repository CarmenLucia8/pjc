import discord
import random
from discord.ext import commands
from datetime import datetime
import locale

# Configura o locale para português do Brasil
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# Configura o bot com o prefixo de comando "!"
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.dm_messages = True  # Habilita a recepção de mensagens diretas
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs de configuração do servidor
BOT_TOKEN = "MTI5NzI4NjM1OTYxODI5MzgwMQ.GQYAUE.7VQkNrCuKoGh-EVnBDROJZ2QObqLxx_-CXL2-U"
CATEGORIA_ID = 1297951712824262696  # ID da categoria onde os processos serão criados
CANAL_ID = 1297269257188671522  # ID do canal onde a mensagem será enviada
ADDITIONAL_CHANNEL_ID = 1297422399255613511  # ID do canal adicional para notificação de novos processos
ROLE_ID = 1297665855970349177

# Evento quando o bot está pronto
@bot.event
async def on_ready():
    print(f"Bot está online como {bot.user}")

    # Busca a categoria e canal onde os processos serão criados
    guild = discord.utils.get(bot.guilds)
    ticket_category = discord.utils.get(guild.categories, id=CATEGORIA_ID)
    channel = discord.utils.get(guild.text_channels, id=CANAL_ID)

    if channel is None:
        print(f"Canal com ID {CANAL_ID} não encontrado.")
        return

    # Cria um embed para a mensagem inicial com o menu suspenso
    embed = discord.Embed(
        title="🌟 Bem-vindo ao PJc • Justiça Unificada Capital City 🌟",
        description=(
            "Processo Judicial Eletrônico - Acompanhe processos judiciais independentemente de tramitações.\n\n"
            "🛑 **Atenção:** Todos os processos devem ser ajuizados de acordo com as normas vigentes. "
            "Escolha a espécie do processo que deseja ajuizar usando o menu abaixo:"
        ),
        color=discord.Color.from_rgb(255, 140, 0)  # Laranja mais escuro
    )

    # Adiciona a imagem ao embed
    image_url = "https://i.ibb.co/sWLMHmH/PROCESSO-ELETR-NICO-DA-CAPITAL.png"  # Teste com outro link de imagem funcional
    embed.set_image(url=image_url)

    # Envia a mensagem embed no canal com a imagem
    await channel.send(embed=embed, view=SpeciesDropdownView(ticket_category))

# Criação de um menu suspenso (dropdown) para a escolha de espécie de processo
class SpeciesDropdown(discord.ui.Select):
    def __init__(self, ticket_category):
        self.ticket_category = ticket_category
        # Define as opções do menu suspenso
        options = [
            discord.SelectOption(label="AÇÃO PENAL - COMUM", description="Ajuizar uma Ação Penal - Comum", emoji="⚖️"),
            discord.SelectOption(label="AÇÃO PENAL - EXTRAORDINÁRIA", description="Ajuizar uma Ação Penal - Extraordinária", emoji="⚔️"),
            discord.SelectOption(label="ALVARÁ DE FUNCIONAMENTO", description="Ajuizar um Alvará de Funcionamento", emoji="📜"),
            discord.SelectOption(label="AUTORIZAÇÃO PORTE DE ARMA DE FOGO", description="Ajuizar uma Autorização para Porte de Arma de Fogo", emoji="🔫"),
            discord.SelectOption(label="LIMPEZA DE FICHA", description="Ajuizar uma Limpeza de Ficha", emoji="🧹"),
            discord.SelectOption(label="PROCEDIMENTO COMUM CÍVEL", description="Ajuizar um Procedimento Comum Cível", emoji="📃"),
            discord.SelectOption(label="REMÉDIOS CONSTITUCIONAIS", description="Ajuizar um Remédio Constitucional", emoji="📗")
        ]
        super().__init__(placeholder="Escolha a espécie do processo...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        species = self.values[0]
        emoji = next(option.emoji for option in self.options if option.label == species)
        await interaction.response.send_modal(ProcessInfoModal(self.ticket_category, species, emoji))

# Modal interativo para coletar as informações do processo
class ProcessInfoModal(discord.ui.Modal):
    def __init__(self, ticket_category, species, emoji):
        super().__init__(title="Informações do Processo")
        self.ticket_category = ticket_category
        self.species = species
        self.emoji = emoji

        # Campos do modal
        self.add_item(discord.ui.TextInput(label="Advogado", placeholder="Nome do Advogado"))
        self.add_item(discord.ui.TextInput(label="Requerente", placeholder="Nome do Requerente"))
        self.add_item(discord.ui.TextInput(label="Requerido", placeholder="Nome do Requerido"))
        self.add_item(discord.ui.TextInput(label="Causa de Pedir", placeholder="Descreva a causa de pedir"))

    async def on_submit(self, interaction: discord.Interaction):
        advogado = self.children[0].value
        requerente = self.children[1].value
        requerido = self.children[2].value
        causa_pedir = self.children[3].value

        if self.ticket_category is None:
            await interaction.response.send_message(f"A categoria de tramitação ainda não foi configurada.", ephemeral=True)
            return

        # Gera o número do processo sem o emoji e os caracteres 「」
        process_number = f"{random.randint(100000, 999999)}-{datetime.now().month:02d}-{datetime.now().year}"

        # Obtém a data e hora atual
        now = datetime.now()
        formatted_date = now.strftime("%d/%m/%Y às %Hh%Mmin")

        try:
            # Cria um novo canal dentro da categoria definida com o número do processo e o emoji
            guild = interaction.guild
            process_channel = await guild.create_text_channel(f"「{self.emoji}」{process_number}", category=self.ticket_category)

            # Envia notificação ao canal adicional
            additional_channel = discord.utils.get(guild.text_channels, id=ADDITIONAL_CHANNEL_ID)
            if additional_channel is not None:
                additional_embed = discord.Embed(
                    title="📂 Novo Processo Ajuizado",
                    description=(
                        f"**Classe:** {self.species}\n"
                        f"**Autos n.°:** {process_number}\n"
                        f"**Advogado(s):** {advogado}\n"
                        f"**Requerente:** {requerente}\n"
                        f"**Requerido:** {requerido}\n"
                        f"Para mais detalhes, clique no canal: {process_channel.mention}"
                    ),
                    color=discord.Color.blue()
                )
                await additional_channel.send(embed=additional_embed)

            # Cria um embed para a mensagem simples com as informações do processo
            from discord import ButtonStyle, ui

            class ProcessView(discord.ui.View):
                def __init__(self):
                    super().__init__()

                @discord.ui.button(label="🛠️ Distribuir", style=discord.ButtonStyle.primary)  # Cor azul
                async def distribute(self, interaction, button):
                    role = interaction.message.guild.get_role(ROLE_ID)  # Obtém o cargo pelo ID
                    member = interaction.user

                    if member:
                        if role in member.roles:
                            # Remove o cargo se já tiver
                            channel = bot.get_channel(interaction.channel.id)
                            await member.remove_roles(role)
                            button.label = "🛠️ Distribuir"

                            await interaction.response.edit_message(view=self)
                            await channel.send(f"```{datetime.now().strftime('%d/%m/%Y | %Hh%Mmin')} - Autos Incluídos no Juízo 100% Digital```")
                            await channel.send(f"```{datetime.now().strftime('%d/%m/%Y | %Hh%Mmin')} - Distribuído por Sorteio```")
                        else:
                            # Adiciona o cargo se não tiver
                            await member.add_roles(role)

                            button.label = "📨 Anexar"
                            await interaction.response.edit_message(view=self)

                @discord.ui.button(label="✅ Habilitar", style=discord.ButtonStyle.primary)  # Cor azul
                async def enable(self, button: discord.ui.Button, interaction: discord.Interaction):
                    await interaction.response.send_message("Habilitar ainda não implementado.", ephemeral=True)

                @discord.ui.button(label="❌ Desabilitar", style=discord.ButtonStyle.primary)  # Cor azul
                async def disable(self, button: discord.ui.Button, interaction: discord.Interaction):
                    await interaction.response.send_message("Desabilitar ainda não implementado.", ephemeral=True)

                @discord.ui.button(label="👨‍⚖️ Despachar", style=discord.ButtonStyle.primary)  # Cor azul
                async def dispatch(self, button: discord.ui.Button, interaction: discord.Interaction):
                    await interaction.response.send_message("Despachar ainda não implementado.", ephemeral=True)

                @discord.ui.button(label="🔰️ Transitar", style=discord.ButtonStyle.primary)  # Cor azul
                async def transit(self, button: discord.ui.Button, interaction: discord.Interaction):
                    await interaction.response.send_message("Transitar ainda não implementado.", ephemeral=True)

            embed_with_image = discord.Embed(
                title="📌 Processo Judicial PJc • Justiça Unificada Capital City",
                description=(
                    f"> Processo: **{causa_pedir}**\n"
                    f"> Classe: **{self.species}**\n"
                    f"> Autos n.°: **{process_number}**\n"
                    f"> Órgão Julgador: **VARA ÚNICA DA PROVÍNCIA DE CAPITAL CITY**\n"
                    f"> Advogado(s): **{advogado}**\n"
                    f"> Requerente: **{requerente}**\n"
                    f"> Requerido: **{requerido}**"
                ),
                color=discord.Color.from_rgb(139, 0, 0)  # Vermelho escuro
            )

            # Envia a mensagem com os botões
            message = await process_channel.send(embed=embed_with_image, view=ProcessView())

            # Cria o tópico de tramitações e juntadas dentro do canal do processo
            await process_channel.create_thread(
                name=f"Tramitações e Juntadas",
                message=message,
                auto_archive_duration=1440  # Arquiva automaticamente após 24 horas
            )

            # Envia uma mensagem no privado do usuário que ajuizou o processo
            await interaction.user.send(
                embed=discord.Embed(
                    title="✅ Seu processo foi criado com sucesso!",
                    description=(
                        f"Você ajuizou um processo de espécie **{self.species}**.\n"
                        f"Para acompanhar, clique no canal: {process_channel.mention}\n"
                        f"Número do Processo: **{process_number}**\n"
                    ),
                    color=discord.Color.green()  # Cor verde para indicar sucesso
                ).set_thumbnail(url="https://i.ibb.co/gMNXGfT/5-Photoroom.png")  # Imagem na mensagem privada

            )
        except discord.Forbidden:
            await interaction.response.send_message("Não tenho permissões suficientes para criar um canal.", ephemeral=True)

# View que contém o dropdown
class SpeciesDropdownView(discord.ui.View):
    def __init__(self, ticket_category):
        super().__init__()
        self.add_item(SpeciesDropdown(ticket_category))

# Inicia o bot
bot.run(BOT_TOKEN)