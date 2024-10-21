(prompt " \nLoad RTW dimension reactors only....Do NOT Run........")
(vl-load-com)

;****************************************
(vlr-command-reactor 
	nil '((:vlr-commandEnded . endCommand)))
(vlr-command-reactor 
	nil '((:vlr-commandCancelled . cancelCommand)))
;******************************************************

;****************************************************

(defun endCommand (calling-reactor endcommandInfo / 
		   thecommandend)
(setq thecommandend (nth 0 endcommandInfo))
(cond
  ((= thecommandend "DIMALIGNED") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "DIMLINEAR") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "DIMANGULAR") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "DIMBASLINE") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "DIMCENTER") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "DIMCONTINUE") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "DIMDIAMETER") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "DIMRADIUS") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "DIMORDINATE") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "LEADER") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandend "BHATCH") (setvar "CLAYER" #rtw_curlayer))

  );cond
 (princ)
);defun
;********************************************************
(defun cancelCommand (calling-reactor cancelcommandInfo / 
		      thecommandcancel)
(setq thecommandcancel (nth 0 cancelcommandInfo))
(cond
  ((= thecommandcancel "DIMALIGNED") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "DIMLINEAR") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "DIMANGULAR") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "DIMBASELINE") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "DIMCENTER") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "DIMCONTINUE") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "DIMDIAMETER") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "DIMRADIUS") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "DIMORDINATE") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "LEADER") (setvar "CLAYER" #rtw_curlayer))
  ((= thecommandcancel "BHATCH") (setvar "CLAYER" #rtw_curlayer))

);cond
(princ)
);defun
;*********************************************************
(princ) 