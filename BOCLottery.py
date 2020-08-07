import random

#This is very much a crude draft of how I imagined we would go through a lottery phase
#Any and all ideas are welcome!
#Be brutal, I'm seriously not commited to anything

initList = ['Lucas', 'Ana', 'Ethan', 'Johnny', 'Aidan', 'Clara']
initWeight = [0, 2, -1, 1, 3, 1] #get these values from SQL db
finalResults = {}
# these two lists should always be the same length
for i in range(len(initList)):
    currRank = 0
    currPerson = initList[i]
    currWeight = initWeight[i]
    currRank = random.randint(0,100) + currWeight #maybe make it out of total number of slots?
    finalResults[currPerson] = currRank
sortedResults = sorted(finalResults.items(), key=lambda x: x[1], reverse=True)
print(sortedResults) #prints the names and their ranks in order
