#! /usr/bin/env python3

import math
import sys

def generateModel(processCount, workTicks, putTicks, debug) :

	s = "" # model
	t = "" # correctness props

	s += "ctmc\n"
	s += "\n"

	s += generateConstants(processCount, workTicks, putTicks)
	s += "\n"

	s += "// *** main process begin ***\n"
	s += "\n"
	s += "// * last _# at labels and variables is always the id of the \"owning\" process "
	s += "//\n"
	s += "\n"
	s += "// * no label is for sync. all are for easyier debugging in the simulator\n"
	s += "\n"
	s += "// * changing read and write rates does not work anymore because we collapsed some of those transitions (optimization)\n"
	s += "\n"

	s += generateProcess(0, processCount)
	s += "\n"

	s += "// *** main process end ***\n\n"

	s += "// *** process labels begin ***\n\n"
	s += generateLabels(processCount)
	s += "\n"
	s += "// *** process labels end ***\n\n"

	s += "// *** process copies begin ***\n\n"
	for p in range(1, processCount) :
		s += generateProcess(p, processCount)
		s += "\n"

	s += "// *** process copies end ***\n\n"

	s += "// *** process rewards begin ***\n\n"
	s += generateRewards(processCount)
	s += "\n"
	s += "// *** process rewards end ***\n\n"

	return s, t

def generateConstants(processCount, workTicks, putTicks) :

	s = ""

	maxDist = 2**math.floor(math.log(processCount-1, 2))

	s = "const process_count = " + str(processCount) + ";\n"

	s += "\n"

	s += "const work_ticks  = " + str(workTicks)  + ";\n"
	s += "const put_ticks   = " + str(putTicks)   + ";\n"

	s += "\n"

	s += "// rates\n"
	s += "const double base_rate = 1000.0;\n"
	s += "const double tick      = base_rate / 1.0;\n"
	s += "const double rare      = tick / 1000000;\n"
	s += "const double work      = tick / work_ticks;\n"
	s += "const double put       = tick / put_ticks;\n"

	s += "\n"

	s += "// process locations\n"
	s += "// all names describe the behaviour of the next transition\n"
	s += "const l_init = 0;\n"
	s += "const l_work = l_init;\n"
	s += "const l_put  = 1;\n"
	s += "const l_wait = 2;\n"
	s += "const l_done = 3;\n"

	return s

def generateProcess(p, processCount) :

	s = ""

	maxDist = 2**math.floor(math.log(processCount-1, 2))

	s += "module process_#\n"

	s += "    l_#      : [l_init..l_done] init l_init;\n"
	s += "    //bar_$fromwhom$_$me$ - an array of bits from whom we will receive\n"
	for i in [2**x for x in range(0, int(math.log(maxDist, 2)) + 1)] :
		s += "    bar_%d_#  : bool             init false;\n" % ((p-i)%processCount)
	if maxDist > 1 :
		s += "    dist_#   : [1..%d]           init 1; // distance\n" % maxDist
	else : #happens at process count 2
		s += "    dist_#   : [1..2]           init 1; // distance\n"

	s += "\n"

	s += "    [work_#]   l_#=l_work                                -> work : (l_#'=l_put);\n"
	s += "\n"

	for dist in [2**x for x in range(0, int(math.log(maxDist, 2)) + 1)] :
		s += "    [put_#_%d]  l_#=l_put  & dist_# = %d                   -> put  : (l_#'=l_wait);\n" % (((p+dist) % processCount), dist)

	s += "\n"

	for dist in [2**x for x in range(0, int(math.log(maxDist, 2)) + 1)] :
		if dist != maxDist :
			s += "    [wait_%d_#] l_#=l_wait & dist_# = %d & bar_%d_#  = true -> tick : (l_#'=l_put) & (dist_#'=dist_#*2);\n" % (((p-dist) % processCount), dist, ((p-dist) % processCount))
		else :
			s += "    [wait_%d_#] l_#=l_wait & dist_# = %d & bar_%d_#  = true -> tick : (l_#'=l_done);\n" % (((p-dist) % processCount), dist, ((p-dist) % processCount))

		s += "    [wait_%d_#] l_#=l_wait & dist_# = %d & bar_%d_# != true -> tick : true;\n" % (((p-dist) % processCount), dist, ((p-dist) % processCount))

	s += "\n"
	s += "    [done_#]   l_#=l_done                                -> rare : true;\n"
	s += "\n"

	s += "    // listen for remote puts\n"
	for i in [2**x for x in range(0, int(math.log(maxDist, 2)) + 1)] :
		s += "    [put_%d_#] true -> (bar_%d_#'=true);\n" % (((p-i) % processCount), ((p-i) % processCount))

	s += "endmodule\n"

	return s.replace('#', str(p))

def generateRewards(processCount) :

	s = ""

	maxDist = 2**math.floor(math.log(processCount-1, 2))

	s += "// state rewards\n"
	s += "rewards \"time\"\n"
	s += "    true : base_rate;\n"
	s += "endrewards\n\n"

	s += "rewards \"time_all_are_working\"\n"
	s += "    all_are_working : base_rate;\n"
	s += "endrewards\n\n"

	s += "rewards \"time_not_all_are_working\"\n"
	s += "    !all_are_working : base_rate;\n"
	s += "endrewards\n\n"

	s += "rewards \"time_one_is_working\"\n"
	s += "    one_is_working : base_rate;\n"
	s += "endrewards\n\n"

	s += "rewards \"time_not_one_is_working\"\n"
	s += "    !one_is_working : base_rate;\n"
	s += "endrewards\n\n"

	s += "rewards \"time_one_is_done\"\n"
	s += "    one_is_done : base_rate;\n"
	s += "endrewards\n\n"

	s += "rewards \"time_not_one_is_done\"\n"
	s += "    !one_is_done : base_rate;\n"
	s += "endrewards\n\n"

	s += "rewards \"time_not_all_are_done\"\n"
	s += "    !all_are_done : base_rate;\n"
	s += "endrewards\n\n"

	s += "rewards \"time_all_are_done\"\n"
	s += "    all_are_done : base_rate;\n"
	s += "endrewards\n\n"

	for r in range(0, int(math.log(maxDist, 2)) + 1) :
		s += "rewards \"time_up_to_round_%d_one\"\n" % r
		s += "    up_to_round_%d_one : base_rate;\n" % r
		s += "endrewards\n\n"

	for r in range(0, int(math.log(maxDist, 2)) + 1) :
		s += "rewards \"time_up_to_round_%d_all\"\n" % r
		s += "    up_to_round_%d_all : base_rate;\n" % r
		s += "endrewards\n\n"

	s += "rewards \"remote_transfer\"\n"
	for i in range(0, processCount) :
		for j in [(i + dist) % processCount for dist in [2**x for x in range(0, int(math.log(maxDist, 2)) + 1)]] :
			s += "    [put_%d_%d] true : 1;\n" % (i, j)
	s += "endrewards\n\n"

	s += "\n" + operationRewards("all_are_working", processCount)

	s += "\n" + operationRewards("one_is_working", processCount)

	s += "\n" + operationRewards("not_one_is_done", processCount)

	s += "\n" + operationRewards("not_all_are_done", processCount)

	for r in range(0, int(math.log(maxDist, 2)) + 1) :
		s += "\n" + operationRewards("up_to_round_%d_one" % r, processCount)
		s += "\n" + operationRewards("up_to_round_%d_all" % r, processCount)

	return s

def operationRewards(guard, processCount) :

	s = ""

	maxDist = 2**math.floor(math.log(processCount-1, 2))

	if guard.startswith("not_") :
		guardName = "!" + guard[4:]
	else :
		guardName = guard
	localRewardName = "local_operations_" + guard
	remoteRewardName = "remote_operations_" + guard

	s += "rewards \"%s\"\n" % localRewardName
	for p in range(0, processCount) :
		for dist in [2**x for x in range(0, int(math.log(maxDist, 2)) + 1)] :
			s += "    [wait_%d_%d] %s  : %d;\n" % ((p-dist) % processCount, p, guardName, 1)
	s += "endrewards\n"

	s += "rewards \"%s\"\n" % remoteRewardName
	for p in range(0, processCount) :
		for dist in [2**x for x in range(0, int(math.log(maxDist, 2)) + 1)] :
			s += "    [put_%d_%d] %s : %d;\n" % (p, (p + dist) % processCount, guardName, 1)
	s += "endrewards\n"

	# module process_#                                                                                     # (local ops, remote ops)
	#
	# [put_#_%d]  l_#=l_put  & dist_# = %d                    -> put  : (l_#'=l_wait)                      # (0, 1)
	#
	#if dist != maxDist :
	# [wait_%d_#] l_#=l_wait & dist_# = %d & bar_%d_#  = true -> tick : (l_#'=l_put) & (dist_#'=dist_#*2)  # (1, 0)
	#else
	# [wait_%d_#] l_#=l_wait & dist_# = %d & bar_%d_#  = true -> tick : (l_#'=l_done)                      # (1, 0)
	#
	# [wait_%d_#] l_#=l_wait & dist_# = %d & bar_%d_# != true -> tick : true                               # (1, 0)
	#
	# [done_#]   l_#=l_done                                   -> rare : true                               # (0, 0)
	#
	# endmodule

	return s

def generateLabels(processCount) :

	s = ""

	maxDist = 2**math.floor(math.log(processCount-1, 2))

	s += "formula one_is_done       = " + " | ".join(["l_%d = l_done" % i for i in range(0, processCount)]) + ";\n"
	s += "formula all_are_done      = " + " & ".join(["l_%d = l_done" % i for i in range(0, processCount)]) + ";\n"
	#s += "formula exactly_one_is_done          = " +  " | ".join([ "(l_%d = l_done & " % i + " & ".join(["l_%d < l_done" % j for j in range(0, processCount) if j!=i]) + ")" for i in range(0, processCount)]) + ";\n"
	#s += "label \"one_is_done\"                  = one_is_done;\n"
	#s += "label \"all_are_done\"                 = all_are_done;\n"
	#s += "label \"exactly_one_is_done\"          = exactly_one_is_done;\n"

	s += "\n"

	s += "formula one_is_working    = " +  " | ".join([ "l_%d = l_work" % i for i in range(0, processCount)]) + ";\n"
	s += "formula all_are_working   = " +  " & ".join([ "l_%d = l_work" % i for i in range(0, processCount)]) + ";\n"
	##s += "formula exactly_one_is_done_working  = " +  " | ".join([ "(l_%d >= l_atomic_begin & " % i + " & ".join(["l_%d = l_work" % j for j in range(0, processCount) if j!=i]) + ")" for i in range(0, processCount)]) + ";\n"
	#s += "label \"one_is_working\"               = one_is_working;\n"
	#s += "label \"all_are_working\"              = all_are_working;\n"
	#s += "label \"exactly_one_is_done_working\"  = exactly_one_is_done_working;\n"

	s += "\n"

	for r in range(0, int(math.log(maxDist, 2)) + 1) :
		if r < int(math.log(maxDist, 2)) :
			s += "formula round_%d_one       = !all_are_working & !one_is_done  & (" % r + " | ".join([ "dist_%d  = %d" % (p, 2**r) for p in range(0, processCount)]) + ") & !(" + " | ".join(["round_%d_one" % s for s in range(r+1, int(math.log(maxDist, 2)) + 1)]) + ");\n"
			s += "formula round_%d_all       = !one_is_working  & !all_are_done & (" % r + " & ".join([ "dist_%d >= %d" % (p, 2**r) for p in range(0, processCount)]) + ") & !(" + " | ".join(["round_%d_all" % s for s in range(r+1, int(math.log(maxDist, 2)) + 1)]) + ");\n"
		else :
			s += "formula round_%d_one       = !all_are_working & !one_is_done  & (" % r + " | ".join([ "dist_%d  = %d" % (p, 2**r) for p in range(0, processCount)]) + ");\n"
			s += "formula round_%d_all       = !one_is_working  & !all_are_done & (" % r + " & ".join([ "dist_%d >= %d" % (p, 2**r) for p in range(0, processCount)]) + ");\n"

		#s += "label \"round_%d_one\" = round_%d_one;\n" % (r, r)
		#s += "label \"round_%d_all\" = round_%d_all;\n" % (r, r)
		s += "\n"

	for r in range(0, int(math.log(maxDist, 2)) + 1) :
		if r == 0 :
			s += "formula up_to_round_%d_one = all_are_working   | round_%d_one;\n" % (r, r)
			s += "formula up_to_round_%d_all = one_is_working    | round_%d_all;\n" % (r, r)
		else :
			s += "formula up_to_round_%d_one = up_to_round_%d_one | round_%d_one;\n" % (r, r-1, r)
			s += "formula up_to_round_%d_all = up_to_round_%d_all | round_%d_all;\n" % (r, r-1, r)

	return s

# ### correctness props ### ###################################################
def generateCorrectnessProperties(processCount) :

	t = ""

	maxDist = 2**math.floor(math.log(processCount-1, 2))

	t += "// *** process begin ***\n\n"

	t += "P>=1 [F all_are_done]\n"
	t += "\n"

	for p in range(0, processCount) :
		t += "P>=1 [G ((l_%d=l_done => (" % p + " & ".join(["bar_%d_%d=true" % (from_, p) for from_ in [(p-2**x) % processCount for x in range(0, int(math.log(maxDist, 2)) + 1)]]) + ")))]"

	t += "// the following queries partition the state space and have to add up to the total state count\n"
	t += "filter(+, P=? [all_are_working]) + filter(+, P=? [one_is_done]) + " + " + ".join(["filter(+, P=? [round_%d_one])" % r for r in range(0, int(math.log(maxDist, 2)) + 1)]) + "\n"
	t += "filter(+, P=? [one_is_working]) + filter(+, P=? [all_are_done]) + " + " + ".join(["filter(+, P=? [round_%d_all])" % r for r in range(0, int(math.log(maxDist, 2)) + 1)]) + "\n"

	t += "\n"

	remoteTransferCount = processCount * math.ceil(math.log(processCount, 2))

	t += "// number of remote transfers is fixed to n*ceil(log2(n)) = %d\n" % remoteTransferCount
	t += "R{\"remote_transfer\"}<=%d [F all_are_done] & R{\"remote_transfer\"}>=%d [F all_are_done]\n" % (remoteTransferCount, remoteTransferCount)

	t += "\n"

	t += "// *** process end ***\n"

	return t

# ### quantitative props ### ##################################################
def generateQuantitativeProperties(processCount) :

	t = ""

	maxDist = 2**math.floor(math.log(processCount-1, 2))

	t += "// *** process begin ***\n\n"

	t += "// python source contains comments on queries as well\n"
	t += "\n"
	t += "// e for expected value\n"
	t += "// c for cumulative\n"
	t += "// p for partition\n\n"

	# sascha queries A-D begin
	t += "// sascha queries A-D begin\n\n"

	basicQueries = {
		#key : [query, comment]
		"A" : ["time_not_all_are_working" , "time up to: first finished working and entered"],            # correct
		"B" : ["time_not_one_is_working"  , "time up to: last finished working and entered"],             # correct
		"C" : ["time_one_is_done"         , "time up to: first recognized the barrier is full and left"], # correct
		"D" : ["time_all_are_done"        , "time up to: all recognized the barrier is full and left"],   # correct
		}

	# D-B is probably R{\"time_all_are_done\"}=? [I=time2]), where time2 = time-R{\"time_one_is_working\"}=? [I=time]\n"
	# prose: you subtract the time which at least one is working from the x-axis of the query for all done
	# You can't query like that. It is very possible to do in a script though. Making sure it is correct is hard.

	for k in sorted(basicQueries.keys()) :
		query = basicQueries[k]
		t += "// (%s) and (%se) %s\n" % (k, k, query[1])
		t += "R{\"%s\"}=? [I=time] / base_rate\n" % query[0]                              # correct
		# invers of label %s. reachability reward until the label holds, or during the invers of the label holds
		t += "R{\"time\"}=? [F all_are_done] - R{\"%s\"}=? [F all_are_done]\n" % query[0] # correct
		t += "\n"

	t += "\n"

	t += "// sascha queries A-D end\n\n"

	# ### cumulative queries begin
	# shows how much time has been spent in different parts of the algorithm
	# if simulated up to a certain point
	#
	# in order for cumulative queries to make sense here we have to invert some labels
	t += "// cumulative queries begin\n\n"

	queries = [
		#[key, query, comment]
		["Ac", "time_all_are_working" , "time up to: first finished working and entered"],
		["Bc", "time_one_is_working"  , "time up to: last finished working and entered"],
		["Cc", "time_not_one_is_done" , "time up to: first recognized the barrier is full and left"],
		["Dc", "time_not_all_are_done", "time up to: all recognized the barrier is full and left"],
	]
	for r in range(0, int(math.log(maxDist, 2)) + 1) :
		queries.insert(-2, ["%dc" % r, "time_up_to_round_%d_one" % r, "time up to: first entered round %d" % (r+1)])
		queries.insert(-2, ["%dc" % r, "time_up_to_round_%d_all" % r, "time up to: last entered round %d" % (r+1)])

	for query in queries :
		t += "// (%s) and (%se) %s\n" % (query[0], query[0], query[2])
		t += "R{\"%s\"}=? [C<=time]\n" % query[1]
		t += "R{\"%s\"}=? [F all_are_done]\n" % query[1]
		t += "\n"

	t += "// cumulative queries end\n\n"
	# ### cumulative queries end

	# ### operation counting queries begin
	t += "// operation countingqueries begin\n\n"

	queries = [
		#[key, query, comment]
		["Al", "local_operations_all_are_working"     , "local operations up to: first finished working and entered"],
		["Ar", "remote_operations_all_are_working"    , "remote operations up to: first finished working and entered"],
		["Bl", "local_operations_one_is_working"      , "local operations up to: last finished working and entered"],
		["Br", "remote_operations_one_is_working"     , "remote operations up to: last finished working and entered"],
		["Cl", "local_operations_not_one_is_done"     , "local operations up to: first recognized the barrier is full and left"],
		["Cr", "remote_operations_not_one_is_done"    , "remote operations up to: first recognized the barrier is full and left"],
		["Dl", "local_operations_not_all_are_done"    , "local operations up to: all recognized the barrier is full and left"],
		["Dr", "remote_operations_not_all_are_done"   , "remote operations up to: all recognized the barrier is full and left"],
	]
	for r in range(0, int(math.log(maxDist, 2)) + 1) :
		queries.append(["%dol" % r, "local_operations_up_to_round_%d_one" % r, "time up to: first entered round %d" % (r+1)])
		queries.append(["%dor" % r, "remote_operations_up_to_round_%d_one" % r, "time up to: first entered round %d" % (r+1)])
		queries.append(["%dal" % r, "local_operations_up_to_round_%d_all" % r, "time up to: last entered round %d" % (r+1)])
		queries.append(["%dar" % r, "remote_operations_up_to_round_%d_all" % r, "time up to: last entered round %d" % (r+1)])

	for query in queries :
		t += "// (%s) and (%se) %s\n" % (query[0], query[0], query[2])
		t += "R{\"%s\"}=? [C<=time]\n" % query[1]
		t += "R{\"%s\"}=? [F all_are_done]\n" % query[1]
		t += "\n"

	t += "// operation counting queries end\n\n"
	# ### operation counting queries end

	t += "const double time=ticks/base_rate;\n"
	t += "const double ticks;\n"

	t += "\n"

	t += "// *** process end ***\n"

	return t

# ### helper ### ##############################################################
def everyProcessButMyself (p, processCount) :
	l = []
	for j in range(0, processCount):
		if p != j:
			l += [j]
	return l

def forMe(p, processCount) :
	#me and all but one other
	l = []
	for fromWhom in range(0, processCount) :
		if fromWhom != p :
			s = ""
			for forWhom in range(0, processCount) :
				if forWhom != fromWhom :
					s += str(forWhom)
			l += [s]
	return l

# #############################################################################
helpMessage = \
"""
 gen.py [OPTIONS] [outfile-prefix]

  -h, --help              print help message
  -n <nr>                 set process count
  --work  <ticks>         set tick count for a work period        [default 1]
  --put   <ticks>         set tick count for a remote write (put) [default 100]

  --debug                                                         [default False]
"""

if __name__ == "__main__":

	processCount = 0
	filePrefix = modelFileName = correctnessPropertiesFileName = quantitativePropertiesFileName = ""

	workTicks  = 1
	putTicks   = 100
	debug = False

	i = 1
	while i < len(sys.argv):
		if sys.argv[i] == "-h" or sys.argv[i] == "--help":
			print (helpMessage)
			exit(0)
		elif sys.argv[i] == "-n" or sys.argv[i] == "--processes":
			processCount = int(sys.argv[i+1])
			i += 1
		elif sys.argv[i] == "--work":
			workTicks = int(sys.argv[i+1])
			i += 1
		elif sys.argv[i] == "--put":
			putTicks = int(sys.argv[i+1])
			i += 1
		elif sys.argv[i] == "--debug":
			debug = True
		elif sys.argv[i].startswith("--") :
			print ("unknown parameter: " + sys.argv[i])
			exit(-1)
		elif filePrefix == "":
			filePrefix = sys.argv[i]
			modelFileName = filePrefix + ".pm"
			correctnessPropertiesFileName = filePrefix + "-correctness.props"
			quantitativePropertiesFileName = filePrefix + "-quantitative.props"
		else :
			print ("unknown parameter: " + sys.argv[i])
			exit(-1)
		i += 1

	if len(filePrefix) == 0 :
		print(helpMessage)
		exit(0)

	assert processCount >= 2
	assert workTicks   >= 1
	assert putTicks    >= 1

	modelString = ""
	correctnessPropertiesString = ""

	modelString, correctnessPropertiesString = generateModel(processCount, workTicks, putTicks, debug)

	correctnessPropertiesString  = generateCorrectnessProperties(processCount)

	quantitativePropertiesString = generateQuantitativeProperties(processCount)

	f = open(modelFileName, 'w')
	f.write(modelString)
	f.close()

	f = open(correctnessPropertiesFileName, 'w')
	f.write(correctnessPropertiesString)
	f.close()

	f = open(quantitativePropertiesFileName, 'w')
	f.write(quantitativePropertiesString)
	f.close()

