
class CustomizedField:
    def __init__(self,
                 enum: str = None):
        self.enum = enum


custom_attributes = {
    'BaseItemTypes.dat': {
        'ModDomain': CustomizedField(
            enum='MOD_DOMAIN',
        ),
        'SiteVisibility': CustomizedField(
            enum='BaseItemTypeVisibility',
        ),
    },
    'BestiaryRecipeComponent.dat': {
        'BeastRarity': CustomizedField(
            enum='RARITY',
        ),
    },
    'BetrayalUpgrades.dat': {
        'BetrayalUpgradeSlotsKey': CustomizedField(
            enum='BETRAYAL_UPGRADE_SLOTS',
        ),
    },
    'CraftingBenchOptions.dat': {
        'CraftingBenchCustomAction': CustomizedField(
            enum='CraftingBenchCustomActions',
        ),
    },
    'DelveUpgrades.dat': {
        'DelveUpgradeTypeKey': CustomizedField(
            enum='DELVE_UPGRADE_TYPE',
        ),
    },
    'GrantedEffectsPerLevel.dat': {
        'CooldownBypassType': CustomizedField(
            enum='CooldownBypassTypes',
        ),
    },
    'HarvestObjects.dat': {
        'ObjectType': CustomizedField(
            enum='HARVEST_OBJECT_TYPES',
        ),
    },
    'MapFragmentMods.dat': {
        'MapFragmentFamilies': CustomizedField(
            enum='MAP_FRAGMENT_FAMILIES',
        ),
    },
    'Mods.dat': {
        'Domain': CustomizedField(
            enum='MOD_DOMAIN',
        ),
        'GenerationType': CustomizedField(
            enum='MOD_GENERATION_TYPE',
        ),
    },
    'Scarabs.dat': {
        'ScarabType': CustomizedField(
            enum='SCARAB_TYPES',
        ),
    },
    'ShopPaymentPackage.dat': {
        'ShopPackagePlatform': CustomizedField(
            enum='SHOP_PACKAGE_PLATFORM',
        ),
    },
    'SupporterPackSets.dat': {
        'ShopPackagePlatform': CustomizedField(
            enum='SHOP_PACKAGE_PLATFORM',
        ),
    },
    'Words.dat': {
        'Wordlist': CustomizedField(
            enum='WORDLISTS',
        ),
    },
}
