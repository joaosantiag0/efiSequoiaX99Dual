/*
 * SSDT-PLUG — injeta plugin-type=1 no primeiro processador.
 * Plataforma: Xeon E5 v3/v4 (Haswell-EP / Broadwell-EP) em placas X99.
 * Caminho assumido: \_SB.PR00 (padrão na maioria das X99, inclusive chinesas).
 *
 * Se o seu DSDT declarar os processadores em \_SB.SCK0.CP00 (algumas placas
 * Supermicro/Asus), use o arquivo SSDT-PLUG-ALT.dsl desta mesma pasta.
 */
DefinitionBlock ("", "SSDT", 2, "ACDT", "CpuPlug", 0x00003000)
{
    External (_SB_.PR00, ProcessorObj)

    Scope (\_SB.PR00)
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
