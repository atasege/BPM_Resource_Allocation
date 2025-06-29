#                         start  end   stepsize    Policy       days    processes     selection stragegy problem
python -u src/test.py      1.2  2.3    0.05       Hungarian      365        4            fastest Helpdesk       2>&1 | tee out.txt
