import pandas as pd
import argparse
import sys
import random

#[['Spell_Name', 'Level', 'School']]
df = pd.read_csv("5E_Spells.csv")
no_repeats = pd.DataFrame(dtype=object).reindex_like(df).dropna()
no_repeats['Level']=no_repeats.Level.astype('int64')

def autoSpellbook(iLvl,iSchool,iVerb,iNum,iCan,iFilter,iQuer,iDistr):
	#load in csv
	spell_list = pd.read_csv("5E_Spells.csv")
	spell_list = spell_list[spell_list.Level<=iLvl]
	if not args.cantrip:
		spell_list = spell_list[spell_list.Level!=0]
	if args.school and not args.distribution:#-s and -d both slice df, making them incompatible together. See next if:
		spell_list = schoolSort(spell_list,iSchool,iNum)[0]
	if args.distribution:#distribute() will pass to school sort if needed
		if args.school:
			spell_list = distribute(spell_list,iDistr,iNum,iLvl,iSchool)
		else:
			spell_list = distribute(spell_list,iDistr,iNum,iLvl,False)
	if not iVerb==['Spell_Name', 'Level', 'School']:
		iVerb = ['Spell_Name', 'Level', 'School', 'Casting_Time', 'Range', 'Duration', 'Concentration']
	if args.query:
		for i,quer in enumerate(iQuer):
			iQuer[i] = quer.title()
		iVerb = iVerb + iQuer
	return spell_list.sample(n=iNum).sort_values([iFilter.capitalize(),"Level"])[iVerb].reset_index()


def schoolSort(spell_list,iSchool,iNum):
	school_spells = spell_list[spell_list.School==iSchool[0].capitalize()]
	non_school_spells = spell_list[spell_list.School!=iSchool[0].capitalize()]
	varskew = int(iNum*(float(iSchool[1])/100))
	crazy_dict = {"non_school_spells":non_school_spells,"iNum":iNum,"varskew":varskew,"school_spells":school_spells}
	formula = lambda non_school_spells,iNum,varskew,school_spells: non_school_spells.sample(n=(iNum-varskew)).append([school_spells.sample(n=(varskew))])
	#formula = "{non_school_spells}.sample(n=({iNum}-varskew)).append([{school_spells}.sample(n=(varskew))])".format(
	# non_school_spells=non_school_spells,iNum=iNum,school_spells=school_spells)
	spell_list = failSafe(formula,varskew,crazy_dict)[0]
	return spell_list, school_spells, non_school_spells

def distribute(skew_list,distr,iNum,iLvl,iSchool):
	percent_dict = {"average":[.0,.16,.14,.13,.12,.11,.1,.09,.08,.07],
					"high":[.0,.06,.07,.08,.09,.11,.13,.14,.15,.17],
					"low":[.0,.2,.18,.16,.14,.12,.1,.08,.06,.04],
					"even":[.0,.12,.11,.11,.11,.11,.11,.11,.11,.11],}
	percent_list = percent_dict[distr]
	percent_list = percent_list[0:iLvl+1]
	newmax = float(sum(percent_list))
	if newmax != 1:
		for i,perc in enumerate(percent_list):
			percent_list[i] = (float(perc)/newmax)
	if iSchool:
		varskew = int(iNum*(float(iSchool[1])/100))
		school_spells = schoolSort(skew_list,iSchool,iNum)[1]
		crazy_dict = {"iLvl":iLvl,"school_spells":school_spells,"varskew":varskew,"school_spells":school_spells,"percent_list":percent_list}
		formula = lambda iLvl,varskew,school_spells,percent_list: applySkew(iLvl,varskew,school_spells,percent_list)
		# formula = "applySkew({iLvl},{varskew},{school_spells},{percent_list})".format(
		# iLvl=iLvl,varskew=varskew,school_spells=school_spells,percent_list=percent_list)
		school_spells = failSafe(formula,varskew,crazy_dict)[0]
		varskew = failSafe(formula,varskew,crazy_dict)[1]
		non_school_spells = schoolSort(skew_list,iSchool,iNum)[2]
		non_school_spells = applySkew(iLvl,iNum-varskew,non_school_spells,percent_list)
		# print "PRINTING THE TWO LISTS THAT CONTAIN ALL SPELLS"
		# print non_school_spells
		# print school_spells
		return school_spells.append(non_school_spells)
	return applySkew(iLvl,iNum,skew_list,percent_list)
	
def applySkew(iLvl,iNum,skew_list,percent_list):
	global no_repeats
	# print no_repeats
	# print skew_list
	spell_list = pd.DataFrame(dtype=object).reindex_like(skew_list).dropna()
	spell_list['Level']=spell_list.Level.astype('int64')
	# print no_repeats.empty
	for i in range(1,iLvl+1):
		hold_list = skew_list[skew_list.Level==i].sample(n=int(iNum*percent_list[i]))
		spell_list = spell_list.append([hold_list])
	remainder = range(iNum-len(spell_list))
	no_repeats = no_repeats.append(spell_list)
	# print no_repeats [['Spell_Name', 'Level', 'School']]
	# print skew_list [['Spell_Name', 'Level', 'School']]
	for i in remainder:
		# print "ENTERING THE CURSED LOOP"
		hold_list = skew_list[skew_list.Level==(remainder[i]+1)].sample(n=1)
		# print hold_list[['Spell_Name', 'Level', 'School']]
		spell_list = spell_list.append([hold_list])
	# print skew_list[skew_list.Level<=3]
	# print spell_list
	return spell_list
	
def failSafe(formula,varskew,crazy_dict):
	toggle = True
	while toggle:
		try:
			if "varskew" in crazy_dict.keys():
				crazy_dict["varskew"] = varskew
			output=formula(**crazy_dict)
			toggle = False
		except ValueError:
			varskew = varskew-1
	return output,varskew

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Automatically generates a Wizard's spellbook")
	# parser.add_argument("-cl", "--caster_level", help="Limits output to within Wizard's caster level and known # of spells", type=int)
	parser.add_argument("-sl", "--spell_level", dest="spell_level", help="Limits output to <= spell level give", type=int, choices=range(0,10), default=4)
	parser.add_argument("-s", "--school", help="first argument defines a school of magic, the second defines percent of spells that will be from chosen school", nargs=2, metavar=("SCHOOL","PERCENT"))
	parser.add_argument("-v", "--verbose", help="Output includes more spell info", action="store_true", default=['Spell_Name', 'Level', 'School'])
	parser.add_argument("-n", "--number", help="The number of output spells", type=int, default=20)
	parser.add_argument("-z", "--cantrip", help="Output includes zero level spells", action="store_true")
	parser.add_argument("-f", "--filter", help="Filter output by category", default="Level")
	parser.add_argument("-q", "--query", help="Add requested field to output", action="append", default=[])
	parser.add_argument("-d", "--distribution", help="Determines the level spread of output spells", choices=["low","average","high","even"])
	# parser.add_argument("-w", "--wizard", help="Prints an instance of the Wizard class")
	args = parser.parse_args()
	print autoSpellbook(args.spell_level,args.school,args.verbose,args.number,args.cantrip,args.filter,args.query,args.distribution)

	
