from engine import _call_bielik

insult = input("Zniewaga dziewczyny: ").strip()
my_response = input("Moja odpowiedź (Enter aby pominąć): ").strip()

print("\nAnalizuję...\n")

result = _call_bielik(insult, my_response)

analysis = result["insult_analysis"]
print(f"Poziom gniewu dziewczyny: {analysis['percentage']}%")
print(f"  {analysis['comment']}\n")

if "my_response_analysis" in result:
    mine = result["my_response_analysis"]
    print(f"Poziom obraźliwości mojej odpowiedzi: {mine['percentage']}%")
    print(f"  {mine['comment']}\n")

print("--- Propozycje odpowiedzi ---")
for s in result["suggestions"]:
    print(f"[{s['percentage']:>3}%] {s['text']}")