from weldcore.skill_asset import WeldSkillPackage, package_from_sample
from weldcore.transfer.package import package_from_sample as existing_package_from_sample
from weldcore.model.skill import WeldSkillPackage as ExistingWeldSkillPackage


def test_skill_asset_facade_reexports_existing_package_contract():
    assert WeldSkillPackage is ExistingWeldSkillPackage
    assert package_from_sample is existing_package_from_sample
