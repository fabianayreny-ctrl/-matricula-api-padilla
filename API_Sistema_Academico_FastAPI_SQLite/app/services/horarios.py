from fastapi import HTTPException


def dias_como_conjunto(dias: str) -> set[str]:
    return {dia.strip().upper() for dia in dias.replace(",", "-").split("-") if dia}


def horarios_se_cruzan(
    dias_a: str,
    inicio_a: str,
    fin_a: str,
    dias_b: str,
    inicio_b: str,
    fin_b: str,
) -> bool:
    mismos_dias = bool(dias_como_conjunto(dias_a) & dias_como_conjunto(dias_b))
    horas_superpuestas = inicio_a < fin_b and fin_a > inicio_b
    return mismos_dias and horas_superpuestas


def validar_choques_seccion(
    conexion,
    periodo_id: int,
    docente_id: int,
    aula_id: int | None,
    dias: str,
    hora_inicio: str,
    hora_fin: str,
    excluir_seccion_id: int | None = None,
) -> None:
    parametros: list[object] = [periodo_id]
    exclusion = ""
    if excluir_seccion_id is not None:
        exclusion = "AND id <> ?"
        parametros.append(excluir_seccion_id)

    secciones = conexion.execute(
        f"""
        SELECT id, codigo, docente_id, aula_id, dias, hora_inicio, hora_fin
        FROM secciones
        WHERE periodo_id = ? AND estado <> 'FINALIZADA' {exclusion}
        """,
        parametros,
    ).fetchall()

    for seccion in secciones:
        if not horarios_se_cruzan(
            dias,
            hora_inicio,
            hora_fin,
            seccion["dias"],
            seccion["hora_inicio"],
            seccion["hora_fin"],
        ):
            continue
        if seccion["docente_id"] == docente_id:
            raise HTTPException(
                409,
                f"El docente ya tiene la sección {seccion['codigo']} en ese horario",
            )
        if aula_id is not None and seccion["aula_id"] == aula_id:
            raise HTTPException(
                409, f"El aula ya está ocupada por la sección {seccion['codigo']}"
            )

