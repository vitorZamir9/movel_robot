import java.lang.Thread.sleep
import java.io.PrintStream
import java.io.FileOutputStream
import java.io.FileDescriptor
fun main (){
    System.setOut(PrintStream(FileOutputStream(FileDescriptor.out), true, "UTF-8"))
    println("Olá, esse script vai apresentar a atividade: Revisão Completa — Algoritmos em Kotlin ")
    val contatos = mutableMapOf<Int, Pair<String, String>>()
    var funcao = 0
    var funcaoDif = 0
    var contador= 0
    var numero = 0
    var nome = ""
    val cursos = listOf(
        Curso(1, "Kotlin Básico", "Programação", 40, 8.5, true),
        Curso(2, "Jetpack Compose", "Android", 32, 9.4, true),
        Curso(3, "Room Database", "Android", 24, 8.0, true),
        Curso(4, "Figma Mobile", "Design", 20, 7.5, false),
        Curso(5, "Testes Unitários", "Qualidade", 30, 8.8, true),
        Curso(6, "Coroutines", "Kotlin", 28, 9.0, true)
    )
    while (funcao == 0) {
        println("(0)-funcao" +
                "\n(1)-Exercício 1 — Par ou ímpar" +
                "\n(2)-Exercício 2 — Classificação de nota" +
                "\n(3)-Exercício 3 — Validação de curso" +
                "\n(4)-Exercício 4 — Buscar curso por ID" +
                "\n(5)-Exercício 5 — Filtrar cursos ativos" +
                "\n(6)-Exercício 6 — Ranking por nota" +
                "\n(7)-Exercício 7 — Agrupar por categoria" +
                "\n(8)-Exercício 8 — Calcular carga horária total" +
                "\n(9)-Exercício 9 — Deduplicar categorias" +
                "\n(10)-Exercício 10 — Desafio integrador")
        println("Digite o número da função que você deseja: ")
        var funcao = readln().toInt()
        if (funcao == 0) {
            println("Programa sendo encerrad!")
            break
        }
        if (funcao == 1) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    println("Digite um número para ver se é par ou ímpar: ")
                    var numero = readln().toInt()
                    println("O número: $numero é ${parOuImpar(numero)}")
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao == 2) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    println("Digite o nome do Aluno(a) de Kris: ")
                    var nome = readln().toString()
                    println("Digite a nota final do Aluno(a) $nome: ")
                    var numero = readln().toInt()
                    print("O Aluno de Kris foi: ${aprovacaoDkris(numero)}")
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao == 3) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    println("Digite o nome do Aluno(a) de Kris: ")
                    var nome = readln().toString()
                    println("Digite a carga horária do Aluno(a) $nome: ")
                    var numero = readln().toString()
                    println("A carga horaria do Aluno(a) $nome: ${medicaoCargaHoraria(nome,numero)}")
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao == 4) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    println("Digite um número de 1-10 para saber sobre um curso: ")
                    var numero = readln().toInt()
                    if (buscarPorId(cursos, numero) == null){
                        println("Id de curso inválido!")
                    }else{
                        println("Busca do curso: ${buscarPorId(cursos, numero)}")
                    }
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao == 5) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    println("Todos os cursos ativos:" +
                            "\n${filtrarAtivos(cursos).joinToString(separator = ",\n", prefix = "[", postfix = "]")}\n")
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao == 6) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    println("Todos os cursos por ordem decrescente de acordo pela nota:" +
                            "\n${rankingPorNota(cursos).joinToString(separator = ",\n", prefix = "[", postfix = "]")}\n")
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao == 7) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    val cursosAgrupados = agruparPorCategoria(cursos)
                    println("Cursos Agrupados por Categoria:\n")
                    cursosAgrupados.forEach { (categoria, listaDeCursos) ->
                        println("■ Categoria: $categoria")
                        val cursosFormatados = listaDeCursos.joinToString(
                            separator = ",\n  ", prefix = "  [", postfix = "]\n"
                        )
                        println(cursosFormatados)
                    }
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao == 8) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    println("Soma de todas as cargas horária dos cursos:" +
                            "\n${calcularCargaTotalAtiva(cursos)}Horas")
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao == 9) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    println("Todos os cursos únicos:" +
                            "\n${listarCategoriasUnicas(cursos)}")
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao == 10) {
            //entra no loop da atividade
            while (funcaoDif == 0) {
                //entra no loop da atividade
                println("(0)-Para sair da atividade" +
                        "\n(1)-Para ver a atividade")
                println("Digite aqui um número para continuar: ")
                var funcaoDif = readln().toInt()
                if (funcaoDif == 0) {//Sai da atividade
                    println("Você está saindo da atividade!")
                    sleep(2000)
                    break
                }
                if (funcaoDif == 1) {//Faz a atividade
                    println("Fazendo a atividade!")
                    //Atividade
                    println("\n--- BEM-VINDO AO MINI SISTEMA DE ANÁLISE DE CURSOS ---")
                    println("(1)-Buscar curso por Nome" +
                            "\n(2)-Filtrar cursos por Categoria" +
                            "\n(3)-Ranking geral por Nota" +
                            "\n(4)-Resumo Estatístico por Categoria" +
                            "\n(5)-Validar e Cadastrar Novo Curso" +
                            "\n(6)-Visualizar Teste de Mesa")
                    println("Digite o número da opção do sistema que você deseja: ")
                    val opcaoSistema = readln().toInt()

                    if (opcaoSistema == 1) {
                        println("Digite o nome (ou parte do nome) do curso: ")
                        val busca = readln()
                        val resultados = cursos.filter { it.nome.contains(busca, ignoreCase = true) }
                        if (resultados.isEmpty()) {
                            println("Nenhum curso encontrado com esse nome.")
                        } else {
                            println("Cursos encontrados:\n${resultados.joinToString(",\n")}")
                        }
                    }

                    if (opcaoSistema == 2) {
                        println("Digite a categoria que deseja filtrar: ")
                        val cat = readln()
                        val resultados = cursos.filter { it.categoria.equals(cat, ignoreCase = true) }
                        if (resultados.isEmpty()) {
                            println("Nenhum curso encontrado nessa categoria.")
                        } else {
                            println("Cursos na categoria $cat:\n${resultados.joinToString(",\n")}")
                        }
                    }

                    if (opcaoSistema == 3) {
                        println("--- RANKING DE CURSOS POR NOTA ---")
                        val ranking = rankingPorNota(cursos)
                        ranking.forEachIndexed { index, curso ->
                            println("${index + 1}º - ${curso.nome} | Nota: ${curso.nota} (${curso.categoria})")
                        }
                    }

                    if (opcaoSistema == 4) {
                        println("--- RESUMO POR CATEGORIA ---")
                        val agrupados = agruparPorCategoria(cursos)
                        agrupados.forEach { (categoria, lista) ->
                            val qtd = lista.size
                            val mediaNota = lista.map { it.nota }.average()
                            val totalHoras = lista.sumOf { it.cargaHoraria }
                            println("Categoria: $categoria")
                            println("  - Quantidade de cursos: $qtd")
                            println("  - Média das notas: ${String.format("%.2f", mediaNota)}")
                            println("  - Carga horária total: ${totalHoras}h\n")
                        }
                    }

                    if (opcaoSistema == 5) {
                        println("--- CADASTRO DE NOVO CURSO ---")
                        println("Nome do curso: ")
                        val novoNome = readln()
                        println("Carga horária: ")
                        val novaCargaStr = readln()

                        val validacao = medicaoCargaHoraria(novoNome, novaCargaStr)

                        if (validacao == "Curso Válido") {
                            println("Sucesso: O curso passou na validação e está pronto para ser inserido!")
                            println("Dados validados -> Nome: $novoNome, Carga: ${novaCargaStr}h")
                        } else {
                            println("Erro no cadastro: $validacao")
                        }
                    }

                    if (opcaoSistema == 6) {
                        println("\n=== TESTE DE MESA DOCUMENTADO ===")
                        println("-------------------------------------------------------------------------")
                        println("FUNÇÃO 1: rankingPorNota(cursos)")
                        println("Entrada (Lista original): 6 cursos desordenados [8.5, 9.4, 8.0, 7.5, 8.8, 9.0]")
                        println("Processamento: sortedByDescending { it.nota }")
                        println("Saída esperada (Notas ordenadas): [9.4, 9.0, 8.8, 8.5, 8.0, 7.5]")
                        println("Status do Teste: OK (Verificado na Opção 3)")
                        println("-------------------------------------------------------------------------")
                        println("FUNÇÃO 2: medicaoCargaHoraria(nome, cargaHorariaTEXTO)")
                        println("Caso de Teste A: nome=\"\", carga=\"40\" -> Saída Esperada: \"Nome vazio\"")
                        println("Caso de Teste B: nome=\"Kotlin\", carga=\"-5\" -> Saída Esperada: \"Carga horária deve ser maior que zero\"")
                        println("Caso de Teste C: nome=\"Kotlin\", carga=\"abc\" -> Saída Esperada: \"Carga horária deve ser numérica\"")
                        println("Caso de Teste D: nome=\"Kotlin\", carga=\"120\" -> Saída Esperada: \"Curso Válido\"")
                        println("Status do Teste: OK (Verificado na Opção 5)")
                        println("-------------------------------------------------------------------------\n")
                    }

                    if (opcaoSistema < 1 || opcaoSistema > 6) {
                        println("Opção inválida no sistema de análise.")
                    }
                    //
                    sleep(2000)
                }
            }
        }
        if (funcao >= 11) {//função não definida
            println("Essa função não existe!")
            sleep(2000)
        }

    }
}
fun parOuImpar(numero: Int): String {
    if (numero % 2 == 0) {
        return "Par"
    }else {
        return "Ímpar"
    }

}
fun aprovacaoDkris(numeroPmedia: Int): String {
    if (numeroPmedia >= 90 && numeroPmedia <= 100) {
        return "Excelente"
    }else if (numeroPmedia >= 70 && numeroPmedia <= 89) {
        return "Aprovado"
    }else if (numeroPmedia >= 50 && numeroPmedia <= 69) {
        return "Para Recuperação"
    }else if (numeroPmedia >= 0 && numeroPmedia <= 49) {
        return "Reprovado"
    }else{
        return "Nota inválida"
    }
}
fun medicaoCargaHoraria(nome: String, cargaHorariaTEXTO: String): String {
    val carga = cargaHorariaTEXTO.toIntOrNull()
        ?: return "Carga horária deve ser numérica"
    if (nome == "") {
        return "Nome vazio"
    }else if (carga < 0 ) {
        return "Carga horária deve ser maior que zero"
    }else if (carga > 400) {
        return "Carga horária não pode passar de 400"
    }else{
        return "Curso Válido"
    }
}
data class Curso(
    val id: Int,
    val nome: String,
    val categoria: String,
    val cargaHoraria: Int,
    val nota: Double,
    val ativo: Boolean
)
fun buscarPorId(cursos: List<Curso>, id: Int): Curso? {
    return cursos.firstOrNull { it.id == id }
}
fun filtrarAtivos(cursos: List<Curso>): List<Curso> {
    return cursos.filter { it.ativo }
}
fun rankingPorNota(cursos: List<Curso>): List<Curso> {
    return cursos.sortedByDescending { it.nota }
}
fun agruparPorCategoria(cursos: List<Curso>): Map<String,
        List<Curso>> {
    return cursos.groupBy { it.categoria }
}
fun calcularCargaTotalAtiva(cursos: List<Curso>): Int {
    return cursos
        .filter { it.ativo }
        .sumOf { it.cargaHoraria }
}
fun listarCategoriasUnicas(cursos: List<Curso>): List<String> {
    return cursos
        .map { it.categoria }
        .toSet()
        .toList()
}
