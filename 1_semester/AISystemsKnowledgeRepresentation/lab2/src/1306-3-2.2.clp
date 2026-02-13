(defrule find-student-with-ai-specialization-and-over-20-years-of-age
    (student (name ?name) (age ?age) (spec "ai"))
    (test (>= ?age 20))
    =>
    (printout t "Возраст студента " ?name " " ?age " лет" crlf)
)