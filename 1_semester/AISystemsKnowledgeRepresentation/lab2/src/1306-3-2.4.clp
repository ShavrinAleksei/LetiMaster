(defrule find-student-with-ai-specialization-over-20-years-of-age-with-types-check-and-graduate-from-25-years-old
    (student 
	(name ?name)
	(year ?year & :(integerp ?year))
	(age ?age & :(integerp ?age))
	(spec ?spec & "ai" & :(stringp ?spec))
    )
    (test (>= ?age 20))
    (grad-age =(+ ?age (- 5 ?year)))
    =>
    (printout t ?name " оканчивает университет в возрасте не младше 25 лет" crlf)
)