let shost = "http://127.0.0.1:8732";;
let spkh = "tz1THsLcunLo8CmDm9f2y1xHuXttXZCpyFnq";;

type config = {
	host: string;
	pkh: string
} [@@bs.deriving abstract];;

external load_config: unit -> config = "" [@@bs.val][@@bs.module "../../../config.json"];;
external get: string -> string Js.Promise.t = "get" [@@bs.module "request-promise-native"];;

(* 
	Get the snapshot block for every cycle /chains/main/blocks/head/context/raw/json/rolls/owner/snapshot/7
	Then multiply the result with 256, we get the block of the snapshot
	We get the block hash given its ID
	So we can call host ^ "/chains/main/blocks/" ^ "BMDuEQVnio9imtP2Za3kvSirEptsMYAmoxL2EFExRdgGsq7dc1h" ^ "/context/delegates/" ^ pkh
	And get the snapshot data
*)
let conf = load_config ();;
Js.log @@ (conf |. host);;

let main () =
	get (shost ^ "/chains/main/blocks/" ^ "BMDuEQVnio9imtP2Za3kvSirEptsMYAmoxL2EFExRdgGsq7dc1h" ^ "/context/delegates/" ^ spkh) 
	|> Js.Promise.then_ (fun x ->
		Js.log x;
		get (shost ^ "/chains/main/blocks/head/context/delegates/" ^ spkh)
	) 
	|> Js.Promise.then_ (fun x ->
		Js.log x;
		get (shost ^ "/chains/main/blocks/head/context/contracts/KT1KQhhaJdjysa2ihdNeXCsCFsekQM4PoDzA")
	)
	|> Js.Promise.then_ (fun x ->
		Js.log x;
		get (shost ^ "/chains/main/blocks/head/context/raw/json/rolls/owner/snapshot/7")
	) 
	|> Js.Promise.then_ (fun x ->
		Js.log x;
		Js.Promise.resolve()
	)
	;;
;;


main ();;
