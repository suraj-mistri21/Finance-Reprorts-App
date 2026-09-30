import { redirect } from "react-router";

export const loader = async () => {
  throw redirect("/app");
};

export default function Index() {
  return null;
}