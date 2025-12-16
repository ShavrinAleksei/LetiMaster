(deftemplate student
    (slot name)       ; sudent name (symbol)
    (slot age)        ; student age (integer 17-22)
    (slot year)       ; year of study (integer 2-5)
    (slot spec)       ; specialization (string: "hard", "soft", "ai")
    (slot aver_mark)  ; grade point average (float 3.0-5.0)
)

(deffacts students
    (student (name Alex) (age 21) (year 5) (spec "ai") (aver_mark 5.0))
    (student (name Zakhar) (age 22) (year 2) (spec "ai") (aver_mark 5.0))
    (student (name Michael) (age 20) (year 3) (spec "ai") (aver_mark 5.0))
    (student (name Margarita) (age 19) (year 2) (spec "ai") (aver_mark 4.8))
    (student (name Vlad) (age 17) (year 2) (spec "soft") (aver_mark 4.5))
    (student (name Ilya) (age 19) (year 3) (spec "soft") (aver_mark 4.0))
    (student (name Semen) (age 21) (year 5) (spec "soft") (aver_mark 3.0))
    (student (name Oleg) (age 21) (year 4) (spec "hard") (aver_mark 4.7))
    (student (name Igor) (age 18) (year 2) (spec "hard") (aver_mark 3.5))
    (student (name Alexander) (age 20) (year 4) (spec "hard") (aver_mark 4.0))
)

(deffacts graduation-ages
    (grad-age 25)
)