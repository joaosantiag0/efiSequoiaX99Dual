/*
 * SSDT-SBUS-MCHC (OPCIONAL) — declara o device MCHC no barramento SMBus.
 * Corrige "AppleSMBusPCI" ausente e melhora leitura de temperatura/ventoinha
 * via SMCSuperIO em algumas placas X99.
 *
 * Caminho \_SB.PCI0.SBUS é o mais comum em X99. Verifique no seu DSDT antes.
 */
DefinitionBlock ("", "SSDT", 2, "ACDT", "MCHC", 0x00001000)
{
    External (_SB_.PCI0.SBUS, DeviceObj)

    Scope (\_SB.PCI0.SBUS)
    {
        Device (MCHC)
        {
            Name (_ADR, Zero)
        }
    }
}
