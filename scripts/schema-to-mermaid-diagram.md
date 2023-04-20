## Building a diagram of the data model.

It's possible to export the built schema to a mermaid diagram, which can be version controlled. Mermaid diagrams are [fully supported by github](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams#creating-mermaid-diagrams).

The way I did it was this:
1. Get the schemacrawler latest docker container:
> docker pull schemacrawler/schemacrawler

2. Enter the container shell
> sudo docker run -v $(pwd):/share --rm -i -t --entrypoint=/bin/bash schemacrawler/schemacrawler

3. Run the following inside the docker container's shell:
> schemacrawler   --server=sqlite --database=/share/db.sqlite3 --info-level=maximum --command script --script-language python --script ./mermaid.py > /share/docs/schema.md
