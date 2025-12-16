(deffunction validate-input (?input-text ?valid-options)
    (while TRUE
        (printout t crlf ?input-text crlf)
        (bind ?input (read))
        (if (member$ ?input ?valid-options)
            then (return ?input)
        )
    )
)

(defrule get-service-type
    =>
    (bind ?service-type (validate-input 
        "System supports only card, contribution or app choices
Enter a service where you face the problem: " 
        (create$ card contribution app)   
    ))
    (assert (service-type ?service-type))
)

(defrule get-card-problem
    (service-type card)
    =>
    (bind ?problem-category (validate-input 
        "System supports only security-threat, technical-failure or provide-info choices.
If nothing suits your case, you may choose option other.
What type of problem happened with your card?" 
        (create$ security-threat technical-failure provide-info other)
    ))
    (assert (problem-category ?problem-category))
)

(defrule get-contribution-problem
    (service-type contribution)
    =>
    (bind ?problem-category (validate-input 
        "System supports only security-threat, technical-failure or provide-info choices.
If nothing suits your case, you may choose option other.
What type of problem happened with your contribution?" 
        (create$ security-threat technical-failure provide-info other)
    ))
    (assert (problem-category ?problem-category))
)

(defrule get-app-problem
    (service-type app)
    =>
    (bind ?problem-category (validate-input 
        "System supports only security-threat, technical-failure or provide-info choices.
If nothing suits your case, you may choose option other.
What type of problem happened with your app?" 
        (create$ security-threat technical-failure provide-info other)
    ))
    (assert (problem-category ?problem-category))
)

(defrule get-technical-failure-card-problem-urgency
    (service-type card)
    (problem-category technical-failure)
    (not (recommendation ?))
    =>
    (bind ?customer-urgency (validate-input 
        "Is your problem critical? (yes or no)" 
        (create$ yes no)
    ))
    (assert (customer-urgency ?customer-urgency))
)

(defrule get-non-trivial-card-problem-urgency
    (service-type card)
    (problem-category other)
    (not (recommendation ?))
    =>
    (bind ?customer-urgency (validate-input 
        "Is your problem critical? (yes or no)" 
        (create$ yes no)
    ))
    (assert (customer-urgency ?customer-urgency))
)

(defrule get-security-threat-contribution-problem-urgency
    (service-type contribution)
    (problem-category security-threat)
    (not (recommendation ?))
    =>
    (bind ?customer-urgency (validate-input 
        "Is your problem critical? (yes or no)" 
        (create$ yes no)
    ))
    (assert (customer-urgency ?customer-urgency))
)

(defrule get-technical-failure-contribution-problem-urgency
    (service-type contribution)
    (problem-category technical-failure)
    (not (recommendation ?))
    =>
    (bind ?customer-urgency (validate-input 
        "Is your problem critical? (yes or no)" 
        (create$ yes no)
    ))
    (assert (customer-urgency ?customer-urgency))
)

(defrule get-non-trivial-contribution-problem-urgency
    (service-type contribution)
    (problem-category other)
    (not (recommendation ?))
    =>
    (bind ?customer-urgency (validate-input 
        "Is your problem critical? (yes or no)" 
        (create$ yes no)
    ))
    (assert (customer-urgency ?customer-urgency))
)

(defrule get-technical-failure-app-problem-urgency
    (service-type app)
    (problem-category technical-failure)
    (not (recommendation ?))
    =>
    (bind ?customer-urgency (validate-input 
        "Is your problem critical? (yes or no)" 
        (create$ yes no)
    ))
    (assert (customer-urgency ?customer-urgency))
)

(defrule set-default-low-urgency-if-not-provided
    (declare (salience -100))
    (service-type ?)
    (problem-category ?)
    (not (customer-urgency ?))
    =>
    (assert (customer-urgency no))
)

(defrule output-card-security-threat-recommendation
    (service-type card)
    (problem-category security-threat)
    (or (customer-urgency yes)
        (customer-urgency no))
    =>
    (printout t crlf "Your card will be blocked. Info sent to security department" crlf)
    (assert (recommendation block-card))
    (assert (notify security-department))
)

(defrule output-card-urgent-technical-failure-recommendation
    (service-type card)
    (problem-category technical-failure)
    (customer-urgency yes)
    =>
    (printout t crlf "Your card will be re-released in two days" crlf)
    (assert (recommendation urgent-card-re-release))
    (assert (notify tech-department))
)

(defrule output-card-non-urgent-technical-failure-recommendation
    (service-type card)
    (problem-category technical-failure)
    (customer-urgency no)
    =>
    (printout t crlf "Your card will be re-released in seven days" crlf)
    (assert (recommendation non-urgent-card-re-release))
    (assert (notify tech-department))
)

(defrule output-card-provide-info-recommendation
    (service-type card)
    (problem-category provide-info)
    (or (customer-urgency yes)
        (customer-urgency no))
    =>
    (printout t crlf "Application to receive information about your card is transmitted for consideration" crlf)
    (assert (recommendation transmit-card-info-application))
    (assert (notify tech-support))
)

(defrule output-card-non-trivial-urgent-problem-recommendation
    (service-type card)
    (problem-category other)
    (customer-urgency yes)
    =>
    (printout t crlf "You will be connected with our contact center in a few minutes to discuss a problem with your card" crlf)
    (assert (recommendation connect-with-contact-center-about-urgent-card-problem))
    (assert (notify contact-center))
)

(defrule output-card-non-trivial-non-urgent-problem-recommendation
    (service-type card)
    (problem-category other)
    (customer-urgency no)
    =>
    (printout t crlf "Our first available operator will recall you to discuss problem with your card" crlf)
    (assert (recommendation connect-with-contact-center-about-non-urgent-card-problem))
    (assert (notify contact-center))
)

(defrule output-urgent-contribution-security-threat-recommendation
    (service-type contribution)
    (problem-category security-threat)
    (customer-urgency yes)
    =>
    (printout t crlf "Your contribution is blocked. All recent operations will be inspected during the next few hours" crlf)
    (assert (recommendation block-contribution-with-fraud-inspection))
    (assert (notify security-department))
)

(defrule output-non-urgent-contribution-security-threat-recommendation
    (service-type contribution)
    (problem-category security-threat)
    (customer-urgency no)
    =>
    (printout t crlf "Your contribution is blocked by standart procedure. All recent operations will be inspected during till tomorrow. Technical support will call you for the next hour" crlf)
    (assert (recommendation block-contribution-suspicious-transactions-inspection))
    (assert (notify security-department))
    (assert (notify tech-support))
)

(defrule output-urgent-contribution-technical-failure-recommendation
    (service-type contribution)
    (problem-category technical-failure)
    (customer-urgency yes)
    =>
    (printout t crlf "Your contribution will be fixed in an hour by tech department." crlf)
    (assert (recommendation transmit-critical-bug-to-tech-department))
    (assert (notify tech-department))
)

(defrule output-non-urgent-contribution-technical-failure-recommendation
    (service-type contribution)
    (problem-category technical-failure)
    (customer-urgency no)
    =>
    (printout t crlf "Your contribution will be fixed till tomorrow by tech department." crlf)
    (assert (recommendation transmit-average-bug-to-tech-department))
    (assert (notify tech-department))
)

(defrule output-contribution-provide-info-recommendation
    (service-type contribution)
    (problem-category provide-info)
    (or (customer-urgency yes)
        (customer-urgency no))
    =>
    (printout t crlf "Application to receive information about your contribution is transmitted for consideration" crlf)
    (assert (recommendation transmit-contribution-info-application))
)

(defrule output-contribution-non-trivial-urgent-problem-recommendation
    (service-type contribution)
    (problem-category other)
    (customer-urgency yes)
    =>
    (printout t crlf "You will be connected with our contact center in a few minutes to discuss a problem with your contribution" crlf)
    (assert (recommendation connect-with-contact-center-about-urgent-contribution-problem))
    (assert (notify contact-center))
)

(defrule output-contribution-non-trivial-non-urgent-problem-recommendation
    (service-type contribution)
    (problem-category other)
    (customer-urgency no)
    =>
    (printout t crlf "Our first available operator will recall you to discuss problem with your contribution" crlf)
    (assert (recommendation connect-with-contact-center-about-non-urgent-contribution-problem))
    (assert (notify contact-center))
)

(defrule output-app-security-threat-recommendation
    (service-type app)
    (problem-category security-threat)
    (or (customer-urgency yes)
        (customer-urgency no))
    =>
    (printout t crlf "You account is temporarily blocked. Information sent to security department" crlf)
    (assert (recommendation block-account))
    (assert (notify security-department))
)

(defrule output-urgent-app-technical-failure-recommendation
    (service-type app)
    (problem-category technical-failure)
    (customer-urgency yes)
    =>
    (printout t crlf "Server-side problems. Retry your attempt in 30 minutes" crlf)
    (assert (recommendation report-about-server-side-problems))
    (assert (notify tech-department))
)

(defrule output-non-urgent-app-technical-failure-recommendation
    (service-type app)
    (problem-category technical-failure)
    (customer-urgency no)
    =>
    (printout t crlf "Your bug will be reported to tech department. Thank you for your feedback." crlf)
    (assert (recommendation report-average-app-bug-to-tech-department))
    (assert (notify tech-department))
)

(defrule output-app-provide-info-recommendation
    (service-type app)
    (problem-category provide-info)
    (or (customer-urgency yes)
        (customer-urgency no))
    =>
    (printout t crlf "User guide is sent on your email" crlf)
    (assert (recommendation send-user-guide))
)

(defrule output-app-non-trivial-problem-recommendation
    (service-type app)
    (problem-category other)
    (or (customer-urgency yes)
        (customer-urgency no))
    =>
    (printout t crlf "You will be connected with our contact center to discuss a problem with your app" crlf)
    (assert (recommendation connect-with-contact-center-about-app-problem))
    (assert (notify contact-center))
)