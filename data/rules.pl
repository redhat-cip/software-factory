check_code_review(Rem, Out):-
  findall(X, gerrit:commit_label(label('Code-Review', 2), Who), List),
  length(List, 2),
  !,
  Out = [label('Code-Review', ok(Who)) | Rem].

check_code_review(Rem, Out):-
  Out = [label('Code-Review', need("2 +2s")) | Rem].

submit_filter(In, Out):-
  In =.. [submit | Ls],
  gerrit:remove_label(Ls, label('Code-Review', _), Rem),
  check_code_review(Rem, Final),
  Out =.. [submit | Final].
