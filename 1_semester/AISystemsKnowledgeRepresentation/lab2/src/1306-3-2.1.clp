(defrule find-student-with-ai-specialization
    (student (name ?name) (year ?year) (spec "ai"))
    =>
    (printout t "—тудент " ?name " учитс€ по специализации УaiФ на " ?year " курсе" crlf)
)