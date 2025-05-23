import discord
from discord.ui import Button, Modal, Select, View
import pytz
from datetime import datetime, timedelta

from config import TIMEZONE_MAPPING, RAID_TEMPLATES
from utils import validate_time_input

class CreateRaidFlow:
    def __init__(self, raid_name: str = None):
        self.raid_name = raid_name
        self.raid_type: str = None
        self.duration: str = None
        self.date: str = None
        self.tz: str = None
        self.start_time_str: str = None

class TimeModal(Modal, title="Enter Raid Time"):
    def __init__(self, flow: CreateRaidFlow):
        super().__init__()
        self.flow = flow
        self.start_time = discord.ui.TextInput(
            label="Start Time",
            placeholder="Use format 6:30PM or 18:30"
        )
        self.add_item(self.start_time)

    async def on_submit(self, interaction: discord.Interaction):
        self.flow.start_time_str = self.start_time.value
        await interaction.response.defer()
        self.stop()

class TimeButton(Button):
    def __init__(self, row: int):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="Enter Time & Create",
            row=row,
            disabled=True
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        # Ensure all dropdowns are filled before proceeding
        if not view.all_required_filled():
            return await interaction.response.send_message(
                "Please complete all dropdown selections first.",
                ephemeral=True
            )

        # Prompt user for exact time
        modal = TimeModal(view.flow)
        await interaction.response.send_modal(modal)
        await modal.wait()

        # Validate the submitted time string
        try:
            user_time = await validate_time_input(view.flow.start_time_str)
        except ValueError as e:
            return await interaction.followup.send(str(e), ephemeral=True)

        # Combine selected date and time, then convert to UTC
        date_obj = datetime.strptime(view.flow.date, "%Y-%m-%d").date()
        local_dt = datetime.combine(date_obj, user_time)
        tz = pytz.timezone(TIMEZONE_MAPPING[view.flow.tz])
        localized_dt = tz.localize(local_dt, is_dst=None)
        start_ts = int(localized_dt.astimezone(pytz.utc).timestamp())
        ping_ts = start_ts - 30 * 60

        # Attach timestamps to flow for the command handler
        view.flow._start_ts = start_ts
        view.flow._ping_ts = ping_ts
        view.submitted = True

        # Signal that input is complete
        view.stop()

class FlowSelect(Select):
    def __init__(self, name: str, options: list[discord.SelectOption], row: int, placeholder: str):
        super().__init__(placeholder=placeholder, row=row, options=options)
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        setattr(self.view.flow, self.name, selected)
        for opt in self.options:
            opt.default = (opt.value == selected)
        view = self.view
        view.time_button.disabled = not view.all_required_filled()
        await interaction.response.edit_message(view=view)

class TimezoneSelect(Select):
    def __init__(self, row: int):
        now = datetime.now(pytz.utc)
        options = []
        for code, zone in TIMEZONE_MAPPING.items():
            if zone == "UTC":
                abbr = "UTC"
            else:
                tz = pytz.timezone(zone)
                local = now.astimezone(tz)
                is_dst = bool(local.dst() and local.dst() != timedelta(0))
                abbr = {
                    "PT": "PDT" if is_dst else "PST",
                    "MT": "MDT" if is_dst else "MST",
                    "CT": "CDT" if is_dst else "CST",
                    "ET": "EDT" if is_dst else "EST",
                    "AT": "AKDT" if is_dst else "AKST",
                }[code]
            options.append(discord.SelectOption(label=abbr, value=code))
        super().__init__(placeholder="Select Timezone", row=row, options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        view = self.view
        view.flow.tz = choice
        for opt in self.options:
            opt.default = (opt.value == choice)
        view.time_button.disabled = not view.all_required_filled()
        await interaction.response.edit_message(view=view)

class CreateRaidView(View):
    def __init__(self, flow: CreateRaidFlow):
        super().__init__(timeout=300)
        self.flow = flow
        
        # Raid type dropdown
        raid_options = [discord.SelectOption(label=k, value=k) for k in RAID_TEMPLATES]
        self.add_item(FlowSelect(name="raid_type", options=raid_options, row=0, placeholder="Select Raid"))

        # Duration dropdown
        duration_options = [discord.SelectOption(label=d, value=d) for d in ("3 hours", "1 hour 30 minutes")]
        self.add_item(FlowSelect(name="duration", options=duration_options, row=1, placeholder="Select Duration"))

        # Date dropdown (next 14 days)
        today = datetime.now()
        date_options = [
            discord.SelectOption(
                label=(today + timedelta(days=i)).strftime("%A, %B %d"),
                value=(today + timedelta(days=i)).strftime("%Y-%m-%d")
            ) for i in range(14)
        ]
        self.add_item(FlowSelect(name="date", options=date_options, row=2, placeholder="Select Date"))

        # Timezone dropdown
        self.add_item(TimezoneSelect(row=3))

        # Time entry button
        self.time_button = TimeButton(row=4)
        self.time_button.disabled = True
        self.add_item(self.time_button)

    def all_required_filled(self) -> bool:
        return all([
            self.flow.raid_type,
            self.flow.duration,
            self.flow.date,
            self.flow.tz
        ])

class UpdateButton(TimeButton):
    def __init__(self, row: int):
        super().__init__(row)
        self.label = "Enter Time & Update"

class UpdateRaidView(CreateRaidView):
    def __init__(self, flow: CreateRaidFlow):
        super().__init__(flow)

        # Remove the raid_type select
        for item in list(self.children):
            if isinstance(item, FlowSelect) and item.name == "raid_type":
                self.remove_item(item)

        # Prefill the remaining dropdowns
        for child in self.children:
            if isinstance(child, FlowSelect):
                for opt in child.options:
                    opt.default = (opt.value == getattr(flow, child.name))
            elif isinstance(child, TimezoneSelect):
                for opt in child.options:
                    opt.default = (opt.value == flow.tz)

        # Relabel the button
        self.time_button.label = "Enter Time & Update"
        
        # Always keep it enabled
        self.time_button.disabled = False

        self.submitted = False

    def all_required_filled(self) -> bool:
        # Override CreateRaidView’s check so the button never auto-disables
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass