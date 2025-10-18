#!/usr/bin/env ruby

c = {}
g = ""
f = $stdin.readlines

t = {
	"bg"  => {namesuffix: "Bulgarian", tag: /\.bg$/     },
	"mkd" => {namesuffix: "Yugoslav",  tag: /\.mkd$/    },
	"pl"  => {namesuffix: "Polish",    tag: /\.pl$/     },
	"zhp" => {namesuffix: "Pinyin",    tag: /\.pinyin$/, replace: {
		"ascript" => "a",
	}},
	"smi" => {namesuffix: "Sami",      swap: {"Eng.var2" => "Eng"}},
	"liv" => {namesuffix: "Livonian",  swap: {
		"Dcommaaccent" => "Dcedilla",
		"dcommaaccent" => "dcedilla"
	}, replace: {
		"Tcommaaccent" => "Tcedilla",
		"tcommaaccent" => "tcedilla",
	}},
	"ro"  => {namesuffix: "Romanian",  swap: {
		"Dcommaaccent" => "Dcedilla",
		"dcommaaccent" => "dcedilla"
	}, replace: {
		"Scommaaccent" => "Scedilla",
		"scommaaccent" => "Scedilla",
		"Tcommaaccent" => "Tcedilla",
		"tcommaaccent" => "tcedilla",
	}},
	"ewe" => {namesuffix: "African",   swap: {"florin" => "fscript.ewe"}},
	"cv"  => {namesuffix: "Chuvash",   tag: /\.cv$/     },
}

f.each {|l|
	l.chomp!
	if l =~ /^StartChar:/ then
		g = l.sub(/^StartChar:\s*(.*)$/, '\1')
	elsif l =~ /^Encoding:/ and g != "" then
		c.merge!({g => l.sub(/^Encoding:\s*(\d+)\s+(-?\d+).*$/, '\2')})
	end
}

c.each {|k, v|
	if (not t[$*[0]][:tag].nil?) and k =~ t[$*[0]][:tag] then
		w = c[k.sub(t[$*[0]][:tag], "")]
		c[k.sub(t[$*[0]][:tag], "")] = v
		c[k] = w
	elsif (not t[$*[0]][:swap].nil?) and (not t[$*[0]][:swap][k].nil?) then
		w = c[t[$*[0]][:swap][k]]
		c[t[$*[0]][:swap][k]] = v
		c[k] = w
	elsif (not t[$*[0]][:replace].nil?) and (not t[$*[0]][:replace][k].nil?) then
		c[k] += "," + c[t[$*[0]][:replace][k]]
		c[t[$*[0]][:replace][k]] = "-1"
	end
}

g = ""
f.each {|l|
	if l =~ /^(Font|Full|Family)Name:/ then
		l.sub!(/Inconsolata( ?)LGC/, '\&\1' + t[$*[0]][:namesuffix])
	elsif l =~ /^StartChar:/ then
		g = l.sub(/^StartChar:\s*(.*)$/, '\1')
	elsif l =~ /^Encoding:/ and g != "" then
		if c[g] !~ /,/ then
			l.sub!(/^Encoding:\s*(\d+)\s*(-?\d+)/, 'Encoding: \1 ' + c[g])
		else
			cs = c[g].split(",")
			l.sub!(/^Encoding:\s*(\d+)\s*(-?\d+)/, 'Encoding: \1 ' + cs[0])
			cs.shift
			cs.each {|a|
				l += format("\nAltUni2: %06x.ffffffff.0", a.to_i)
			}
		end
	end
	begin
		puts l
	rescue Errno::EPIPE
	end
}
