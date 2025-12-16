(assert (car fit) (driver wait) (transaction success))

(deffacts parking "Pay parking system"
	(car fit)
	(driver wait)
	(transaction success)
)

(defrule R1 
	(car fit)
	(driver wait)
	=>
	(printout t crlf "An empty parking spot for waiting driver exists" crlf)
	(assert (spot available))
)
(defrule R2
	(driver wait)
	(transaction success)
	=>
	(printout t crlf "Transaction successfull: a waiting driver paid money for parking" crlf)
	(assert (payment received))
)
(defrule R3
	(spot available)
	(payment received)
	=>
	(printout t crlf "Driver can park the car in the assigned spot" crlf)
	(assert (parking granted))
)
