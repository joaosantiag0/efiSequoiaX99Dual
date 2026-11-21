/*
 * SSDT-USBX — limites de energia das portas USB para desktops.
 * Não depende do caminho de ACPI da placa: funciona em qualquer X99.
 *
 * Valores: 5100 mA (0x13EC) em sleep/wake e 2100 mA (0x834) por porta.
 * Ajuste se a sua placa entrega mais corrente (ex.: 0x1F40 = 8000 mA).
 */
DefinitionBlock ("", "SSDT", 2, "ACDT", "UsbX", 0x00000000)
{
    Scope (\_SB)
    {
        Device (USBX)
        {
            Name (_ADR, Zero)

            Method (_DSM, 4, NotSerialized)
            {
                If ((Arg2 == Zero))
                {
                    Return (Buffer (One) { 0x03 })
                }

                Return (Package (0x08)
                {
                    "kUSBSleepPowerSupply",
                    0x13EC,
                    "kUSBSleepPortCurrentLimit",
                    0x0834,
                    "kUSBWakePowerSupply",
                    0x13EC,
                    "kUSBWakePortCurrentLimit",
                    0x0834
                })
            }
        }
    }
}
