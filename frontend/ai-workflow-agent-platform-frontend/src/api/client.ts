import axios from "axios";

export const runWorkflow = async (query: string) => {
  const res = await axios.post("http://localhost:8000/workflow", {
    query,
  });
  return res.data;
};