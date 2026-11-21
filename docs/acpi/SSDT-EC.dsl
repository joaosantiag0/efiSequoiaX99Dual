/*
 * SSDT-EC (OPCIONAL) — cria um EC falso para que o AppleACPI fique satisfeito
 * em placas desktop X99 que têm apenas um "H_EC" incompleto no DSDT.
 *
 * ATENÇÃO: o caminho \_SB.PCI0.LPCB e o nome EC0 podem conflitar com a sua
 * placa. Só habilite este SSDT se o boot travar em "AppleACPICPU" ou se você
 * vir erros de EC no log. O ideal é gerar este arquivo com o SSDTTime rodando
 * NA MÁQUINA ALVO (ele detecta o caminho certo automaticamente).
 */
DefinitionBlock ("", "SSDT", 2, "ACDT", "SsdtEC", 0x00001000)
{
    External (_SB_.PCI0.LPCB, DeviceObj)

    Scope (\_SB.PCI0.LPCB)
    {
        Device (EC0)
        {
            Name (_HID, EisaId ("PNP0C09"))
            Name (_UID, Zero)
            Name (_GPE, 0x6F)

            Name (CRS, ResourceTemplate ()
            {
                IO (Decode16, 0x0062, 0x0062, 0x00, 0x01)
                IO (Decode16, 0x0066, 0x0066, 0x00, 0x01)
            })

            Method (_CRS, 0, NotSerialized)
            {
                Return (CRS)
            }

            Method (_STA, 0, NotSerialized)
            {
                Return (0x0F)
            }
        }
    }
}
