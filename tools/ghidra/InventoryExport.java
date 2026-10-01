// Inventory export: enumerate the post-analysis symbol universe of the current
// program and write it as deterministic, line-oriented TSV that *seeds* the
// committed symbol ledger (it never *is* the ledger — see docs/architecture.md,
// "Segmentation seed").
//
// Requires a *full auto-analysis* run (do NOT pass -noanalysis): the export is
// only meaningful over Ghidra's post-analysis functions, data, symbols and
// memory blocks.
//
// Usage (headless):
//   analyzeHeadless <projDir> <projName> \
//       -process <program> \
//       -scriptPath <this dir> \
//       -postScript InventoryExport.java <outDir>
//
// <outDir> is created if needed. Four files are written there (all TSV, header
// row, sorted for determinism):
//
//   inventory.tsv           cut-point candidates  -> seeds the ledger manifest
//   inventory.nested.tsv    reference-only symbols -> the review table, never
//                           the manifest (jump tables, literal pools, aliases,
//                           labels inside functions, …)
//   inventory.gaps.tsv      uncovered ranges in initialized blocks -> the
//                           generator fills these as D_<addr> blobs so the
//                           progress denominator is complete
//   inventory.externals.tsv imported symbols (dynsym) -> recorded as the
//                           ledger's first-class "external" kind, excluded from
//                           the progress denominator
//
// Classification rules (this file is the *draft*, not the authority):
//   * every Function in an executable block              -> cut point
//   * every top-level Data in a non-executable block     -> cut point
//     (.rodata/.data)
//   * every other symbol in the program's default space  -> nested
//   * imported symbols (ExternalManager)                 -> external
//   * initialized bytes not claimed by a function body or
//     a defined Data                                     -> gap
//
// One row is emitted per symbol; aliases are NOT deduplicated — resolving an
// alias into a single ledger entry is the ledger generator's job (is_alias
// guard), not this draft's.
// @category Soaratorium

import java.io.File;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.address.AddressRange;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;

public class InventoryExport extends GhidraScript {

    // Fixed-width (8 hex digit) address so lexical sort == numeric sort across
    // the whole image (base 0x60000000 .. 0x62146788).
    private static String addr(Address a) {
        return String.format("%08x", a.getOffset());
    }

    // TSV safety: symbol names carry no tab/newline by contract, but scrub them
    // defensively rather than corrupt a row.
    private static String esc(String s) {
        if (s == null) {
            return "";
        }
        return s.replace('\t', ' ').replace('\r', ' ').replace('\n', ' ');
    }

    // A name is "discovered" only when it came from the binary (imported) or a
    // human (user-defined). Everything else — DEFAULT placeholders and names
    // ANALYSIS derived — is "generated", because Ghidra never decides names
    // (see docs/architecture.md, "Symbol & data naming").
    private static String nameClass(SourceType src) {
        return (src == SourceType.IMPORTED || src == SourceType.USER_DEFINED)
                ? "discovered" : "generated";
    }

    private static String bool(boolean b) {
        return b ? "1" : "0";
    }

    private static void writeTsv(PrintWriter out, String header, List<String[]> rows) {
        out.println(header);
        for (String[] r : rows) {
            out.println(String.join("\t", r));
        }
    }

    // Sort rows by their joined text: the leading fixed-width address (or block
    // name, for gaps) is the primary key, and every following column is a
    // deterministic tie-breaker. No timestamps, no absolute paths, no randomness.
    private static final Comparator<String[]> DET = (a, b) ->
            String.join("\t", a).compareTo(String.join("\t", b));

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            printerr("usage: InventoryExport.java <outDir>");
            return;
        }

        File outdir = new File(args[0]);
        if (!outdir.isDirectory() && !outdir.mkdirs()) {
            printerr("could not create output dir: " + outdir);
            return;
        }

        Listing listing = currentProgram.getListing();
        Memory memory = currentProgram.getMemory();
        SymbolTable symbols = currentProgram.getSymbolTable();
        FunctionManager functions = currentProgram.getFunctionManager();
        AddressSpace defSpace = currentProgram.getAddressFactory().getDefaultAddressSpace();

        // Entry points (loader-known exported entries) — used for the "entry" flag.
        Set<Address> entries = new HashSet<>();
        AddressIterator eit = symbols.getExternalEntryPointIterator();
        while (eit.hasNext()) {
            entries.add(eit.next());
        }

        // ---- Cut-point candidates (functions + non-executable top-level data) ----
        // cutPoints is the set of addresses the manifest owns; the nested pass
        // excludes the *primary* symbol at each of these addresses.
        Set<Address> cutPoints = new HashSet<>();
        List<String[]> main = new ArrayList<>();

        FunctionIterator fit = functions.getFunctions(true);
        while (fit.hasNext()) {
            Function f = fit.next();
            Address ep = f.getEntryPoint();
            if (!ep.getAddressSpace().equals(defSpace)) {
                continue;
            }
            cutPoints.add(ep);
            Symbol sym = f.getSymbol();
            SourceType src = (sym != null) ? sym.getSource() : SourceType.DEFAULT;
            boolean exported = (sym != null) && sym.isGlobal();
            main.add(new String[]{
                    addr(ep),
                    "function",
                    Long.toString(f.getBody().getNumAddresses()),
                    esc(f.getName()),
                    block(memory, ep),
                    src.name(),
                    nameClass(src),
                    bool(f.isThunk()),
                    bool(entries.contains(ep)),
                    bool(exported),
                    bool(f.getBody().getNumAddressRanges() > 1),
            });
        }

        // Top-level data (not contained inside another Data). Route by block:
        // data in a non-executable block is a cut point; data living inside
        // .text (literal pools, jump tables) is reference material and is
        // captured by the symbol pass instead.
        DataIterator dit = listing.getDefinedData(true);
        while (dit.hasNext()) {
            Data d = dit.next();
            Address da = d.getAddress();
            if (!da.getAddressSpace().equals(defSpace)) {
                continue;
            }
            MemoryBlock blk = memory.getBlock(da);
            boolean executable = blk != null && blk.isExecute();
            if (executable) {
                continue;
            }
            cutPoints.add(da);
            Symbol sym = d.getPrimarySymbol();
            SourceType src = (sym != null) ? sym.getSource() : SourceType.DEFAULT;
            String name = (sym != null) ? sym.getName() : ("DAT_" + addr(da));
            boolean exported = (sym != null) && sym.isGlobal();
            main.add(new String[]{
                    addr(da),
                    "data",
                    Integer.toString(d.getLength()),
                    esc(name),
                    block(memory, da),
                    src.name(),
                    nameClass(src),
                    "0",
                    "0",
                    bool(exported),
                    "0",
            });
        }
        Collections.sort(main, DET);

        // ---- Reference-only symbols (nested file) -------------------------------
        List<String[]> nested = new ArrayList<>();
        SymbolIterator sit = symbols.getAllSymbols(true);
        while (sit.hasNext()) {
            Symbol s = sit.next();
            Address sa = s.getAddress();
            if (!sa.getAddressSpace().equals(defSpace)) {
                continue;
            }
            // The primary symbol at a cut-point address is already represented by
            // its function/data row; everything else (aliases, labels inside
            // functions, literal-pool labels, params/locals) is reference material.
            if (s.isPrimary() && cutPoints.contains(sa)) {
                continue;
            }
            Function parent = functions.getFunctionContaining(sa);
            nested.add(new String[]{
                    addr(sa),
                    s.getSymbolType().toString(),
                    esc(s.getName()),
                    block(memory, sa),
                    s.getSource().name(),
                    nameClass(s.getSource()),
                    parent != null ? addr(parent.getEntryPoint()) : "",
            });
        }
        Collections.sort(nested, DET);

        // ---- Gaps (uncovered initialized bytes) ---------------------------------
        // covered = function bodies ∪ defined data (top-level data spans its
        // nested components, so its [min,max] covers struct/array members).
        // Anything else in an initialized block is a gap the generator fills as
        // a D_<addr> blob.
        AddressSet covered = new AddressSet();
        for (Function f : functions.getFunctions(true)) {
            if (f.getEntryPoint().getAddressSpace().equals(defSpace)) {
                covered.add(f.getBody());
            }
        }
        for (Data d : listing.getDefinedData(true)) {
            Address da = d.getAddress();
            if (da.getAddressSpace().equals(defSpace)) {
                covered.add(d.getMinAddress(), d.getMaxAddress());
            }
        }

        List<String[]> gaps = new ArrayList<>();
        for (MemoryBlock blk : memory.getBlocks()) {
            if (!blk.isInitialized()) {
                continue;
            }
            if (!blk.getStart().getAddressSpace().equals(defSpace)) {
                continue;
            }
            AddressSet blockSet = new AddressSet(blk.getStart(), blk.getEnd());
            AddressSet uncovered = blockSet.subtract(covered);
            for (AddressRange r : uncovered.getAddressRanges()) {
                gaps.add(new String[]{
                        blk.getName(),
                        addr(r.getMinAddress()),
                        Long.toString(r.getLength()),
                });
            }
        }
        Collections.sort(gaps, DET);

        // ---- Externals (imports) ------------------------------------------------
        List<String[]> externals = new ArrayList<>();
        SymbolIterator xsit = symbols.getExternalSymbols();
        while (xsit.hasNext()) {
            Symbol s = xsit.next();
            String lib = (s.getParentNamespace() != null)
                    ? s.getParentNamespace().getName() : "";
            externals.add(new String[]{
                    esc(s.getName()),
                    esc(lib),
                    s.getSource().name(),
            });
        }
        Collections.sort(externals, DET);

        // ---- Write --------------------------------------------------------------
        String hdrMain = String.join("\t", "addr", "kind", "size", "name", "block",
                "source", "name_class", "thunk", "entry", "exported", "noncontig");
        String hdrNested = String.join("\t", "addr", "kind", "name", "block",
                "source", "name_class", "parent");
        String hdrGaps = String.join("\t", "block", "addr", "size");
        String hdrExt = String.join("\t", "name", "library", "source");

        try (PrintWriter wMain = new PrintWriter(new File(outdir, "inventory.tsv"));
             PrintWriter wNested = new PrintWriter(new File(outdir, "inventory.nested.tsv"));
             PrintWriter wGaps = new PrintWriter(new File(outdir, "inventory.gaps.tsv"));
             PrintWriter wExt = new PrintWriter(new File(outdir, "inventory.externals.tsv"))) {
            writeTsv(wMain, hdrMain, main);
            writeTsv(wNested, hdrNested, nested);
            writeTsv(wGaps, hdrGaps, gaps);
            writeTsv(wExt, hdrExt, externals);
        }

        println(String.format(
                "InventoryExport: cut=%d nested=%d gaps=%d externals=%d -> %s",
                main.size(), nested.size(), gaps.size(), externals.size(), outdir));
    }

    private static String block(Memory memory, Address a) {
        MemoryBlock b = memory.getBlock(a);
        return b != null ? b.getName() : "?";
    }
}
