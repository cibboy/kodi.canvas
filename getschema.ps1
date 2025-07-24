[CmdletBinding()]
Param (
	[Parameter(Mandatory = $true)]
	[string]$Method,

	[string]$Path = '.\introspect.json'
)

function Get-RecursiveTypeResolution {
	[CmdletBinding()]
	param (
		[Parameter(Mandatory = $true)]
		[PSCustomObject]$Object,
		[Parameter(Mandatory = $true)]
		[PSCustomObject]$Schema
	)

	$ret = [ordered]@{}

	# First resolve type extension.
	$extends = $Object.extends
	if ($null -ne $extends) {
		$recursive = Get-RecursiveTypeResolution -Object $Schema.types.$extends -Schema $Schema
		foreach ($k in $recursive.Keys | Sort-Object) { $ret[$k] = $recursive[$k] }
	}

	# Then add properties.
	foreach ($p in ($Object.properties.psobject.Properties | Where-Object { $_.MemberType -eq 'NoteProperty' } | Sort-Object Name)) {
		# Resolve possible schema references.
		$obj = [ordered]@{}
		foreach ($sp in ($p.Value.psobject.Properties | Where-Object { $_.MemberType -eq 'NoteProperty' } | Sort-Object Name)) {
			if ($sp.Name -eq '$ref') {
				$recursive = Get-RecursiveTypeResolution -Object $Schema.types.($sp.Value) -Schema $Schema
				foreach ($rk in $recursive.Keys | Sort-Object) { $obj[$rk] = $recursive[$rk] }
			}
			else { $obj[$sp.Name] = $sp.Value }
		}

		$ret[$p.Name] = $obj
	}

	# Then add base type properties.
	if ($null -ne $Object.type) { $ret['type'] = $Object.type }
	if ($null -ne $Object.items) { $ret['items'] = $Object.items }

	return $ret
}

function Get-RecursiveMethodResultResolution {
	[CmdletBinding()]
	Param (
		[Parameter(Mandatory = $true)]
		[PSCustomObject]$Object,
		[Parameter(Mandatory = $true)]
		[PSCustomObject]$Schema
	)

	$ret = [ordered]@{}

	foreach ($p in ($Object.psobject.Properties | Where-Object { $_.MemberType -eq 'NoteProperty' } | Sort-Object Name)) {
		if ($p.TypeNameOfValue -eq 'System.Management.Automation.PSCustomObject') {
			# Recursive call.
			$ret[$p.Name] = Get-RecursiveMethodResultResolution -Object $p.Value -Schema $Schema
		}
		else {
			# Resolve schema references.
			if ($p.Name -eq '$ref') {
				$ret['properties'] = Get-RecursiveTypeResolution -Object $Schema.types.($p.Value) -Schema $Schema
			}
			else { $ret[$p.Name] = $p.Value }
		}
	}

	return $ret
}

function Get-RecursiveMethodQueryResolution {
	[CmdletBinding()]
	Param (
		[Parameter(Mandatory = $true)]
		[PSCustomObject[]]$Parameters,
		[Parameter(Mandatory = $true)]
		[PSCustomObject]$Schema
	)

	$ret = @()
	
	foreach ($param in $Parameters) {
		$q = [ordered]@{}

		foreach ($p in ($param.psobject.Properties | Where-Object { $_.MemberType -eq 'NoteProperty' } | Sort-Object Name)) {
			if ($p.TypeNameOfValue -eq 'System.Management.Automation.PSCustomObject') {
				# Recursive call.
				$q[$p.Name] = Get-RecursiveMethodQueryResolution -Parameters $p.Value -Schema $Schema
			}
			elseif ($p.TypeNameOfValue -eq 'System.Object[]') {
				$arr = @()
				# Recursive call.
				foreach ($e in $p.Value) { $arr += Get-RecursiveMethodQueryResolution -Parameters $e -Schema $Schema }
				$q[$p.Name] = $arr
			}
			else {
				# Resolve schema references.
				if ($p.Name -eq '$ref') {
					$q['properties'] = Get-RecursiveTypeResolution -Object $Schema.types.($p.Value) -Schema $Schema
				}
				else { $q[$p.Name] = $p.Value }
			}
		}

		$ret += $q
	}

	return $ret
}

$schema = Get-Content $Path -Raw | ConvertFrom-Json

# Get interested partial schema.
$m = $schema.result.methods.$Method

$result = @{
	query  = Get-RecursiveMethodQueryResolution -Parameters $m.params -Schema $schema.result
	result = Get-RecursiveMethodResultResolution -Object $m.returns.properties -Schema $schema.result
}

return $result