/*
 * SSDT-PLUG (variante ALT) — para placas cujo DSDT declara os CPUs em
 * \_SB.SCK0.CP00 (Supermicro, algumas Asus/Gigabyte X99).
 * Use NO LUGAR de SSDT-PLUG.aml, nunca junto.
 */
DefinitionBlock ("", "SSDT", 2, "ACDT", "CpuPlug", 0x00003000)
{
    External (_SB_.SCK0.CP00, ProcessorObj)

    Scope (\_SB.SCK0.CP00)
    {
        Method (_DSM, 4, NotSerialized)
        {
            If ((Arg2 == Zero))
            {
                Return (Buffer (One) { 0x03 })
            }

            Return (Package (0x02)
            {
                "plugin-type",
                One
            })
        }
    }
}
