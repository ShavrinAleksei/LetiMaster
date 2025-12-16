(defrule find-student-with-ai-specialization-over-20-years-of-age-and-types-check
    (student 
        (name ?name) 
        (age ?age & :(integerp ?age))
	(spec ?spec & "ai" & :(stringp ?spec))
    )
    (test (>= ?age 20))
    =>
    (printout t "Возраст студента " ?name " " ?age " лет" crlf)
)