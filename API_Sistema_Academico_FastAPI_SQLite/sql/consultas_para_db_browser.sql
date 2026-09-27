-- 1. Estudiantes y la carrera a la que pertenecen
SELECT e.cuenta,
       e.nombres || ' ' || e.apellidos AS estudiante,
       c.codigo AS carrera,
       e.estado
FROM estudiantes e
JOIN carreras c ON c.id = e.carrera_id
ORDER BY e.apellidos;

-- 2. Oferta académica con docente, período, aula y horario
SELECT a.codigo AS asignatura,
       a.nombre,
       s.codigo AS seccion,
       d.nombres || ' ' || d.apellidos AS docente,
       p.anio || '-' || p.numero AS periodo,
       au.codigo AS aula,
       s.dias,
       s.hora_inicio || '-' || s.hora_fin AS horario
FROM secciones s
JOIN asignaturas a ON a.id = s.asignatura_id
JOIN docentes d ON d.id = s.docente_id
JOIN periodos p ON p.id = s.periodo_id
LEFT JOIN aulas au ON au.id = s.aula_id
ORDER BY p.anio, p.numero, a.codigo;

-- 3. Cantidad de estudiantes y cupos disponibles por sección
SELECT a.codigo,
       s.codigo AS seccion,
       s.cupo_maximo,
       COUNT(CASE WHEN m.estado <> 'CANCELADA' THEN 1 END) AS matriculados,
       s.cupo_maximo - COUNT(
           CASE WHEN m.estado <> 'CANCELADA' THEN 1 END
       ) AS disponibles
FROM secciones s
JOIN asignaturas a ON a.id = s.asignatura_id
LEFT JOIN matriculas m ON m.seccion_id = s.id
GROUP BY s.id, a.codigo, s.codigo, s.cupo_maximo;

-- 4. Historial académico con nota final
SELECT e.cuenta,
       e.nombres || ' ' || e.apellidos AS estudiante,
       a.codigo AS asignatura,
       p.anio || '-' || p.numero AS periodo,
       m.estado,
       c.nota_final
FROM matriculas m
JOIN estudiantes e ON e.id = m.estudiante_id
JOIN secciones s ON s.id = m.seccion_id
JOIN asignaturas a ON a.id = s.asignatura_id
JOIN periodos p ON p.id = s.periodo_id
LEFT JOIN calificaciones c ON c.matricula_id = m.id
ORDER BY e.cuenta, p.anio, p.numero;

-- 5. Promedio de notas por asignatura
SELECT a.codigo,
       a.nombre,
       ROUND(AVG(c.nota_final), 2) AS promedio,
       COUNT(c.id) AS calificados
FROM asignaturas a
JOIN secciones s ON s.asignatura_id = a.id
JOIN matriculas m ON m.seccion_id = s.id
JOIN calificaciones c ON c.matricula_id = m.id
GROUP BY a.id, a.codigo, a.nombre;

