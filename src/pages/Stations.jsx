import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { getStations, getErrorMessage, unwrapList } from "../services/api";
import StatusBadge from "../components/StatusBadge";
import { LoadingState, ErrorState, EmptyState } from "../components/LoadState";

export default function Stations() {
  const [rows,setRows]=useState([]), [loading,setLoading]=useState(true), [error,setError]=useState("");
  const [search,setSearch]=useState(""), [district,setDistrict]=useState(""), [page,setPage]=useState(1);
  async function load() {
    setLoading(true);setError("");
    try { const res=await getStations({page,page_size:10,search:search||undefined,district:district||undefined});setRows(unwrapList(res.data)); }
    catch(e){setError(getErrorMessage(e));} finally{setLoading(false);}
  }
  useEffect(()=>{load();},[page]);
  function submit(e){e.preventDefault();setPage(1);load();}
  return <div className="page-content">
    <div className="welcome-row"><div><div className="eyebrow">NETWORK DIRECTORY</div><h2>Monitoring stations</h2><p>Search stations and review their reported reliability information.</p></div></div>
    <section className="panel table-panel">
      <form className="filter-bar" onSubmit={submit}><label className="search-box"><Search size={17}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search station name or ID"/></label><input className="filter-input" value={district} onChange={e=>setDistrict(e.target.value)} placeholder="District"/><button className="button primary" type="submit">Apply filters</button></form>
      {loading?<LoadingState/>:error?<ErrorState message={error} onRetry={load}/>:rows.length?<><div className="table-scroll"><table><thead><tr><th>Station</th><th>District</th><th>State</th><th>Reliability score</th><th>Category</th><th>Priority</th><th>Coordinates</th></tr></thead><tbody>{rows.map((s,i)=><tr key={s.station_id??i}><td><b>{s.station_name??"Unnamed station"}</b><small className="sub-cell">{s.station_id??"ID unavailable"}</small></td><td>{s.district??"—"}</td><td>{s.state??"—"}</td><td>{s.reliability_score??"—"}</td><td><StatusBadge value={s.reliability_category}/></td><td><StatusBadge value={s.investigation_priority}/></td><td>{s.latitude!=null&&s.longitude!=null?`${s.latitude}, ${s.longitude}`:"Not available"}</td></tr>)}</tbody></table></div><div className="pagination"><span>Page {page}</span><div><button className="button secondary" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Previous</button><button className="button secondary" onClick={()=>setPage(p=>p+1)}>Next</button></div></div></>:<EmptyState message="No stations found. Try changing the filters or check whether the backend database has been populated."/>}
    </section>
  </div>;
}