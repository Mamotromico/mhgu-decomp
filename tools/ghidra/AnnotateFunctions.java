// Disassemble a set of (address, length) ranges and emit one structured, annotated row
// per instruction. Unlike DisasmFunctions.java (which prints a fixed number of
// instructions from each entry, for human reading), this emits machine-readable TSV so
// tools/loop/bundle.py can resolve branch/literal targets and render the model's context.
//
// It intentionally resolves *addresses and values only* — no symbol names. The committed
// ledger is the naming authority, so name resolution happens in Python (bundle.py), which
// keeps naming consistent with the rest of the tooling.
//
// Usage (headless):
//   analyzeHeadless <projDir> <projName> \
//       -process <program> -noanalysis \
//       -scriptPath <this dir> \
//       -postScript AnnotateFunctions.java <reqFile> <outFile>
//
// <reqFile>: one "addr length" per line; addr is hex (0x-optional), length is decimal or
//            0x-hex. Blank lines and '#' comments ignored.
//
// <outFile> TSV, no header, one row per instruction:
//   addr <TAB> bytes <TAB> mnemonic <TAB> operands <TAB> flows
//   * bytes    — the instruction's raw bytes, lowercase hex, no separators
//   * operands — Ghidra's default operand representation (comma-separated); a
//                pc-relative load appears with its target resolved, e.g. "ldr r0, [0x60001058]"
//   * flows    — comma-separated branch/call target addresses (Ghidra getFlows)
// @category Soaratorium

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.Memory;

public class AnnotateFunctions extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            printerr("usage: AnnotateFunctions.java <reqFile> <outFile>");
            return;
        }

        Memory mem = currentProgram.getMemory();
        try (BufferedReader in = new BufferedReader(new FileReader(args[0]));
             PrintWriter out = new PrintWriter(args[1])) {

            String line;
            while ((line = in.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) {
                    continue;
                }
                String[] parts = line.split("\\s+");
                if (parts.length < 2) {
                    out.println(";; malformed request: " + line);
                    continue;
                }
                long start;
                long length;
                try {
                    start = Long.parseUnsignedLong(parts[0].replaceFirst("^0[xX]", ""), 16);
                    length = parseLength(parts[1]);
                } catch (NumberFormatException e) {
                    out.println(";; malformed request: " + line);
                    continue;
                }
                Address cur = toAddr(start);
                Address end;
                try {
                    if (cur == null) {
                        out.println(";; bad address: " + line);
                        continue;
                    }
                    end = cur.add(length);
                } catch (Exception e) {
                    out.println(";; request out of range: " + line);
                    continue;
                }

                while (cur.compareTo(end) < 0) {
                    if (!mem.contains(cur)) {
                        out.printf("%s\t-\t<no-memory>\t\t\t%n", cur);
                        break;
                    }
                    try {
                        if (!disassemble(cur)) {
                            out.printf("%s\t-\t<undisassembled>\t\t\t%n", cur);
                            break;
                        }
                    } catch (Exception e) {
                        out.printf("%s\t-\t<error:%s>\t\t\t%n", cur, e.getMessage());
                        break;
                    }
                    Instruction ins = getInstructionAt(cur);
                    if (ins == null) {
                        out.printf("%s\t-\t<null>\t\t\t%n", cur);
                        break;
                    }
                    out.printf("%s\t%s\t%s\t%s\t%s%n",
                            ins.getAddress(), hexBytes(mem, ins), ins.getMnemonicString(),
                            operands(ins), flows(ins));
                    cur = ins.getAddress().add(ins.getLength());
                }
            }
        }
        println("AnnotateFunctions: wrote " + args[1]);
    }

    private static long parseLength(String s) {
        if (s.startsWith("0x") || s.startsWith("0X")) {
            return Long.parseUnsignedLong(s.substring(2), 16);
        }
        return Long.parseLong(s);
    }

    private static String hexBytes(Memory mem, Instruction ins) {
        byte[] bs = new byte[ins.getLength()];
        try {
            mem.getBytes(ins.getAddress(), bs);
        } catch (Exception e) {
            return "?";
        }
        StringBuilder sb = new StringBuilder();
        for (byte b : bs) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    private static String operands(Instruction ins) {
        StringBuilder sb = new StringBuilder();
        for (int j = 0; j < ins.getNumOperands(); j++) {
            sb.append(j == 0 ? "" : ", ");
            sb.append(ins.getDefaultOperandRepresentation(j));
        }
        return sb.toString();
    }

    private static String flows(Instruction ins) {
        List<String> list = new ArrayList<>();
        try {
            for (Address f : ins.getFlows()) {
                list.add(f.toString());
            }
        } catch (Exception e) {
            // some instructions throw when flows cannot be computed; treat as none
        }
        return String.join(",", list);
    }
}
