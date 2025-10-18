#!/usr/bin/env ruby

rawlog = `git log --date-order --date=short --pretty=format:"%cd %cN <%cE>%n%n* %s%n" | fold -sw72`

dateauth=""
skipflag=false
logdat=[]

rawlog.each_line do |line|
	line.chomp!
	if skipflag then
		skipflag = false
	elsif line =~ /^\d{4}-\d\d-\d\d / then
		if dateauth != line then
			logdat.push line
		else
			skipflag = true
			logdat.pop
		end
		dateauth = line
	elsif line =~ /^[^\*]/ then
		logdat.push ("\t  " + line)
	elsif line =~ /^\*/ then
		logdat.push ("\t" + line)
	else
		logdat.push line
	end
end

print logdat.join("\n"), "\n"
