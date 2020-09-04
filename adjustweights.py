# a rough draft of how to adjust weights after a trip

'''
Status determines student's results in lottery:
    0: did not sign up
    1: signed up and got it
    2: signed up and didn't get it
    3: signed up and got it but couldn't go
    4: signed up and got it but backed out at last minute
'''

initList = ['Lucas', 'Ana', 'Ethan', 'Johnny', 'Aidan', 'Clara']
initWeight = [0, 2, -1, 1, 3, 1]
initStatus = [0, 1, 2, 3, 4, 2]

for i in range(len(initList)):
    if initStatus[i] == 2:
        initWeight[i] *= 1.1
    elif initStatus[i] == 1:
        initWeight[i] *= .9
    elif initStatus[i] == 4:
        initWeight[i] *= .7

    if initWeight[i] < .25:
        initWeight[i] = .25
    elif initWeight[i] > 5:
        initWeight[i] = 5