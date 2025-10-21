"""User interface elements for setting joint material properties."""
from .forms import Form, SimpleFormDialog
from .forms.fields import LargeFloatField
from .material import JointInterfaceMaterial, Material, joint_material_datastore


class JointMaterialForm(Form):
    """Form for collection of joint element material property parameters."""

    tensile_strength = LargeFloatField(display_name="Tensile Strength")
    internal_friction_coefficient = LargeFloatField(
        display_name="Internal Friction Angle"
    )
    cohesion = LargeFloatField()
    energy_release_rate_mode_1 = LargeFloatField(display_name="GI Energy Release Rate")
    energy_release_rate_mode_2 = LargeFloatField(display_name="GII Energy Release Rate")


class JointMaterialFormDialog(SimpleFormDialog):
    """Dialog for display and processing of JointMaterialForm."""

    def __init__(
        self,
        materials: tuple[Material, Material],
    ):
        """Create a new JointMaterialFormDialog.

        Args:
          materials: materials that have joint eleents at their interface
        """
        self.materials = materials
        try:
            self.joint_material: JointInterfaceMaterial | None = (
                joint_material_datastore.get_by_materials(*materials)
            )
        except ValueError:
            self.joint_material = None
        super().__init__(
            JointMaterialForm,
            initial_data=self.joint_material.properties if self.joint_material else {},
        )

    def _ok_clicked(self) -> None:
        if data := super()._ok_clicked():
            # check whether we need to update or create new
            if self.joint_material:
                self.joint_material.properties = data
            else:
                joint_material_datastore.add(
                    JointInterfaceMaterial(self.materials[0], self.materials[1], data)
                )
            self.close()
