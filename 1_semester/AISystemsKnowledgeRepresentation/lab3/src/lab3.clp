(deffacts initial-facts
   (a)
   (b)
   (c)
   (d)
   (e)
)

(defrule rule1
   (declare (salience 5000))
   (a)
   (b)
   (c)
   =>
   (assert (r))
)

(defrule rule2
   (declare (salience 5000))
   (e)
   (c)
   (d)
   =>
   (assert (p))
)

(defrule rule3
   (declare (salience 5000))
   (a)
   (b)
   =>
   (assert (m))
)

(defrule rule4
   (declare (salience 5000))
   (a)
   (e)
   =>
   (assert (n))
)

(defrule rule5
   (declare (salience 5000))
   (m)
   (n)
   (r)
   =>
   (assert (s))
)

(defrule rule6
   (declare (salience 6000))
   (m)
   (p)
   =>
   (assert (t))
)